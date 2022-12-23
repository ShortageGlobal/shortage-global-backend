from rest_framework import (
    generics,
    viewsets,
    mixins,
    filters,
    permissions,
    exceptions,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from .models import Organization, Instruction, Product, OrganizationBlogPost
from .serializers import (
    OrganizationPreviewSerializer,
    InstructionSerializer,
    PromotedProductPreviewSerializer,
    ProductPreviewSerializer,
    OrganizationBlogPostPreviewSerializer,
    OrganizationBlogPostSerializer,
    OrganizationBlogPostSlugSerializer,
    CategorySerializer,
    OrganizationSerializer,
    OrganizationSlugSerializer,
    ProductSerializer,
    OrganizationProductSlugSerializer,
    PrivateOrganizationSerializer,
    OrganizationRegistrationRequestSerializer,
)
from .exceptions import OneOrganizationPerUser


class PromotedOrganizationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted organizations"""

    queryset = Organization.objects.promoted().order_by("-created_at")
    serializer_class = OrganizationPreviewSerializer


class PromotedProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted products"""

    serializer_class = PromotedProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        queryset = Product.objects.promoted()

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class PromotedCategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of categories of promoted products"""

    queryset = (
        Product.objects.promoted()
        .distinct("category")
        .values_list("category", flat=True)
    )
    serializer_class = CategorySerializer
    paginator = None


class OrganizationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Returns information about specific organization if that organization was verified"""

    schema = AutoSchema(
        tags=["Organizations"],
    )

    queryset = Organization.objects.public()
    serializer_class = OrganizationSerializer
    lookup_field = "slug"


class PrivateOrganizationSlugExistsViewSet(viewsets.ViewSet):
    """
    Checks if organization with specified slug exists
    """

    schema = AutoSchema(
        tags=["Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def retrieve(self, request, slug):
        if Organization.objects.filter(slug=slug).exists():
            return Response(status=status.HTTP_200_OK)
        else:
            raise exceptions.NotFound()


class PrivateOrganizationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Retrieve/create/update organization owned by a current user"""

    schema = AutoSchema(
        tags=["Private", "Organizations"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateOrganizationSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if "retrieve" == self.action or "list" == self.action:
            return Organization.objects.active().filter(owner=self.request.user)
        else:
            # Prevent changes to organizations which you don't own and which are already verified
            return Organization.objects.filter(
                owner=self.request.user, is_verified=False
            )

    def create(self, request, *args, **kwargs):
        # Allow only one organization per user
        if Organization.objects.filter(owner=self.request.user).exists():
            raise OneOrganizationPerUser()

        # Todo: Send an email about organization's creation
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Todo: Send an email about changes to the organization
        return super().update(request, *args, **kwargs)


class InstructionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of instructions that belong to the given organization"""

    serializer_class = InstructionSerializer
    paginator = None

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Instruction.objects.filter(organization=organization)


class ProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of products that belong to the given organization"""

    serializer_class = ProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-top_priority", "position", "-created_at"]

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        queryset = Product.objects.filter(organization=organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class OrganizationBlogPostsViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """A list of blog posts that belong to the given organization"""

    ordering = ["-created_at"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return OrganizationBlogPostPreviewSerializer
        return OrganizationBlogPostSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        queryset = organization.blog_posts.public()
        return queryset

    def perform_destroy(self, instance):
        # TODO: Delete all related images
        super().perform_destroy(instance)


class CategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of categories of the given organization's products"""

    serializer_class = CategorySerializer
    paginator = None

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return (
            Product.objects.filter(organization=organization)
            .distinct("category")
            .values_list("category", flat=True)
        )


class ProductViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Product details for the given slug and the given organization"""

    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.public(), slug=self.kwargs["org_slug"]
        )
        return Product.objects.filter(organization=organization)


class OrganizationRegistrationRequestViewSet(
    mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """Organization Registration Request"""

    schema = AutoSchema(
        tags=["Organizations"],
    )

    permission_classes = [permissions.AllowAny]
    serializer_class = OrganizationRegistrationRequestSerializer


class SitemapViewSet(viewsets.ViewSet):
    """Fetch enitities for sitemap"""

    permission_classes = [permissions.AllowAny]

    @action(detail=False)
    def all_organization_slugs(self, request, *args, **kwargs):
        """Get slugs of public organizations"""
        queryset = Organization.objects.public()
        serializer = OrganizationSlugSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def all_product_slugs(self, request, *args, **kwargs):
        """Get slugs of public products of public organizations"""
        queryset = (
            Product.objects.public()
            .filter(
                organization__is_verified=True,
                organization__is_draft=False,
                organization__is_deleted=False,
            )
            .prefetch_related("organization")
        )
        serializer = OrganizationProductSlugSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def all_blog_post_slugs(self, request, *args, **kwargs):
        """Get slugs of organization blog posts"""
        queryset = (
            OrganizationBlogPost.objects.public()
            .filter(
                organization__is_verified=True,
                organization__is_draft=False,
                organization__is_deleted=False,
            )
            .prefetch_related("organization")
        )
        serializer = OrganizationBlogPostSlugSerializer(queryset, many=True)
        return Response(serializer.data)
