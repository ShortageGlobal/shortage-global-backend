from rest_framework import viewsets, mixins, filters, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework import exceptions
from shortage.apps.catalog.models import Product, Organization
from shortage.apps.catalog.private.serializers import PrivateProductSerializer


class PrivateProductsViewSet(viewsets.ModelViewSet):

    schema = AutoSchema(
        tags=["Private", "Products"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateProductSerializer

    def __init__(self):
        super().__init__()

        self.organization = None

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        queryset = Product.objects.filter(organization=organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def create(self, request, *args, **kwargs):
        # Todo: Change filter to active orgs only!!!!
        self.organization = get_object_or_404(
            Organization.objects.all(), slug=self.kwargs["org_slug"]
        )

        return super().create(request, *args, **kwargs)


class PrivateProductsSlugExistsView(viewsets.ViewSet):
    """
    Checks if a product with the specified slug belongs to the given organization
    """

    schema = AutoSchema(
        tags=["Private", "Products"],
    )

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def retrieve(self, request, org_slug, slug):
        if Product.objects.filter(organization__slug=org_slug, slug=slug).exists():
            return Response(status=status.HTTP_200_OK)
        else:
            raise exceptions.NotFound()
