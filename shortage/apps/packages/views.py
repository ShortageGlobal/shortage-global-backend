import logging
from django.db import transaction
from rest_framework import generics, viewsets, mixins, permissions, exceptions
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.payments import deserialize_stripe_event
from shortage.apps.mailing.mail_service import (
    PackagePaymentStatusUpdatedServiceEmail,
    PackageRegistrationEmail,
)
from .models import Package, Cart, CartItem, PackageStatus
from .package_serializers import (
    PackageSerializer,
    PackageCreationSerializer,
    CorporateDonationSerializer,
)
from .cart_serializers import (
    CartSerializer,
    CartCreationSerializer,
    CartUpdateSerializer,
    CartItemUpdateSerializer,
    CartItemCreationSerializer,
)


def send_email_on_package_status_change(package, organization=None):
    if not package.email:
        return

    if package.status == PackageStatus.REGISTERED:
        package_registration_email = PackageRegistrationEmail(
            organization_slug=organization["org_slug"],
            package_uuid=package.uuid,
            package_type=package.type,
        )
        package_registration_email.add_recipient(
            email=package.email, name=package.full_name
        )
        package_registration_email.send()
    elif (
        package.status == PackageStatus.PAID
        or package.status == PackageStatus.PAYMENT_FAILED
    ):
        email = PackagePaymentStatusUpdatedServiceEmail(package.uuid, package.status)
        email.send()
    elif package.status == PackageStatus.CONFIRMED:
        # Todo: Sent email
        pass
    elif package.status == PackageStatus.DELIVERED:
        # Todo: Send email
        pass


class PackageViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Package details for the given uuid and the given organization"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    serializer_class = PackageSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        user = self.request.user if self.request.user.is_authenticated else None
        return Package.objects.filter(
            items__product__organization=organization, owner=user
        ).distinct()


class PackageCreationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Create package"""

    schema = AutoSchema(
        tags=["Packages"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = PackageCreationSerializer

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.organization = None

    def create(self, request, *args, **kwargs):
        # check organization and store it into view,
        # so serializer could use it for validation
        self.organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )

        package_response = super().create(request, *args, **kwargs)

        uuid = package_response.data["uuid"]
        package = Package.objects.get(uuid=uuid)

        send_email_on_package_status_change(package, self.organization)

        return package_response


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
        user = self.request.user if self.request.user.is_authenticated else None
        queryset = Cart.objects.filter(owner=user)

        if self.action == "retrieve":
            return queryset.prefetch_related(
                "items", "items__product", "items__product__organization"
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
        user = self.request.user if self.request.user.is_authenticated else None
        obj = generics.get_object_or_404(
            CartItem.objects.filter(),
            cart_id=self.kwargs["cart_pk"],
            cart__owner=user,
            pk=self.kwargs.get("pk"),
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def create(self, request, *args, **kwargs):
        user = self.request.user if self.request.user.is_authenticated else None
        # do not add items to a cart of another user
        if not Cart.objects.filter(pk=self.kwargs["cart_pk"], owner=user).exists():
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

        package_uuid = event["data"]["object"]["metadata"]["package_uuid"]
        package = Package.objects.get(uuid=package_uuid)

        if event.type == "payment_intent.succeeded":
            package.payment_succeeded()
            package.save()
        elif event.type == "payment_intent.payment_failed":
            package.payment_failed()
            package.save()
        else:
            logging.info("Unhandled Stripe event type %s", event.type)

        send_email_on_package_status_change(package)

        return Response(status=200)
