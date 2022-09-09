import logging

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core import exceptions
from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import BasePermission

from shortage.apps.catalog.models import Organization
from .models import Package, Cart, CartItem
from .package_serializers import (
    PackageSerializer,
    PackageCreationSerializer,
)
from .cart_serializers import (
    CartSerializer,
    CartCreationSerializer,
    CartItemUpdateSerializer,
    CartItemCreationSerializer,
)
from shortage.apps.mailing.mail_service import PackageRegistrationEmail


class PackageViewSetPermission(BasePermission):
    """
    Allows only authorized GETs
    """

    def has_permission(self, request, view):
        if "GET" == request.method:
            return bool(request.user and request.user.is_authenticated)
        else:
            return True


class PackageViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [PackageViewSetPermission]

    def get_serializer_class(self):
        if "list" == self.action:
            return PackageSerializer
        elif "retrieve" == self.action:
            return PackageSerializer
        elif "create" == self.action:
            return PackageCreationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["organization_slug"] = self.kwargs["org_slug"]

        return context

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        owner = self.request.user

        queryset = (
            Package.objects.all()
            .filter(items__product__organization=organization)
            .distinct()
        )

        if owner.is_authenticated:
            queryset = queryset.filter(owner=owner)
        # For everyone else - return nothing
        else:
            queryset = Package.objects.none()

        return queryset

    def create(self, request, *args, **kwargs):
        package_response = super().create(request, *args, **kwargs)

        uuid = package_response.data["uuid"]
        package = Package.objects.get(uuid=uuid)

        if package.email:
            package_registration_email = PackageRegistrationEmail(
                organization_slug=self.get_serializer_context()["organization_slug"],
                package_uuid=package.uuid,
            )
            package_registration_email.add_recipient(
                email=package.email, name=package.full_name
            )
            package_registration_email.send()

        return package_response


class CartViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Create or retrieve Cart object with related items"""

    permission_classes = [permissions.AllowAny]
    queryset = Cart.objects.prefetch_related(
        "items", "items__product", "items__product__organization"
    ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return CartCreationSerializer
        return CartSerializer


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Create/remove/update CartItem connected to a given Cart"""

    serializer_class = CartItemCreationSerializer
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
        pk = self.kwargs.get("pk")

        try:
            obj = get_object_or_404(
                CartItem.objects.all(), cart_id=self.kwargs["cart_pk"], pk=pk
            )
        except exceptions.ValidationError:
            # in case of invalid uuids show 404 instead of 500
            raise Http404()

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
