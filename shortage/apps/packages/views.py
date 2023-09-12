from django.db import transaction
from rest_framework import generics, viewsets, mixins, permissions, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.schemas.openapi import AutoSchema
from shortage.apps.catalog.models import Organization
from shortage.apps.catalog.serializers import OrganizationBlogPostPreviewSerializer
from shortage.apps.packages.payments import deserialize_stripe_event
from .models import Package, Cart, CartItem
from .package_serializers import (
    PackageSerializer,
    PackageNoteSerializer,
    PackageCreationSerializer,
    CorporateDonationSerializer,
    PackageStatusLogEntrySerializer,
)
from .cart_serializers import (
    CartSerializer,
    CartCreationSerializer,
    CartUpdateSerializer,
    CartItemUpdateSerializer,
    CartItemCreationSerializer,
)


class PackageViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Package details for the given uuid and the given organization"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    permission_classes = [permissions.AllowAny]
    queryset = Package.objects.all()

    def get_serializer_class(self):
        if self.action == "logs":
            return PackageStatusLogEntrySerializer
        if self.action == "leave_note":
            return PackageNoteSerializer
        if self.action == "blog_posts":
            return OrganizationBlogPostPreviewSerializer
        return PackageSerializer

    def get_object(self):
        organization = generics.get_object_or_404(
            Organization.objects.active(), slug=self.kwargs["org_slug"]
        )
        package = generics.get_object_or_404(
            Package.objects.all(),
            pk=self.kwargs["pk"],
            organization=organization,
        )

        # if the package has no owner, just return it
        if package.owner is None:
            return package

        user = self.request.user if self.request.user.is_authenticated else None

        # if unauthenticated user attempts to access package with owner, raise 401
        if user is None:
            raise exceptions.NotAuthenticated()

        # if authenticated user attempts to access package that doesn't belong to them, raise 403
        if user != package.owner and user != organization.owner:
            raise exceptions.PermissionDenied(
                detail="You do not have permission to see this package."
            )

        return package

    @action(detail=True)
    def logs(self, request, *args, **kwargs):
        """Get logs for the package"""
        package = self.get_object()
        queryset = package.status_log.order_by("created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def leave_note(self, request, *args, **kwargs):
        """Leave a note for the organization"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()

    @action(detail=True)
    def blog_posts(self, request, *args, **kwargs):
        """Get blog posts for the package"""
        package = self.get_object()
        queryset = package.blog_posts.published().order_by("-created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PackageCreationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Create package"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = PackageCreationSerializer

    def create(self, request, *args, **kwargs):
        # check organization and store it into view,
        # so serializer could use it for validation
        self.organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )

        return super().create(request, *args, **kwargs)


class CartViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Create or retrieve Cart object with related items"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    http_method_names = ["get", "post", "put", "head", "options"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Cart.objects.all()
        if self.action == "retrieve":
            return queryset.prefetch_related(
                "items",
                "items__product",
                "items__product__organization",
                "items__campaign",
            ).order_by("-created_at")
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return CartCreationSerializer
        if self.action == "update":
            return CartUpdateSerializer
        return CartSerializer


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Create/remove/update CartItem connected to a given Cart"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    http_method_names = ["post", "put", "delete", "head", "options"]
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "update":
            return CartItemUpdateSerializer
        return CartItemCreationSerializer

    def get_serializer_context(self):
        # attach 'cart_pk' to serializer context
        return {
            **super().get_serializer_context(),
            **self.kwargs,
        }

    def get_object(self):
        obj = generics.get_object_or_404(
            CartItem.objects.filter(),
            cart_id=self.kwargs["cart_pk"],
            pk=self.kwargs.get("pk"),
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def create(self, request, *args, **kwargs):
        # do not add items to a cart of another user
        if not Cart.objects.filter(pk=self.kwargs["cart_pk"]).exists():
            raise exceptions.NotFound()
        return super().create(request, *args, **kwargs)


class CorporateDonationsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Corporate Donations"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = CorporateDonationSerializer


class PackagePaymentsWebhookViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def create(self, request, pk=None):
        event = deserialize_stripe_event(
            request.body, request.META["HTTP_STRIPE_SIGNATURE"]
        )
        if event is None:
            raise exceptions.ParseError()

        # retrieve metadata
        package_uuid = event["data"]["object"]["metadata"]["package_uuid"]

        # get package object
        package = generics.get_object_or_404(Package.objects.all(), uuid=package_uuid)

        # Handle the event
        if event["type"] == "payment_intent.canceled":
            package.payment_canceled()
            package.save()
        elif event["type"] == "payment_intent.payment_failed":
            package.payment_failed()
            package.save()
        elif event["type"] == "payment_intent.processing":
            package.payment_processing()
            package.save()
        elif event["type"] == "payment_intent.succeeded":
            package.payment_succeeded()
            package.save()
        else:
            print("Unhandled event type {}".format(event["type"]))

        return Response(status=200)
