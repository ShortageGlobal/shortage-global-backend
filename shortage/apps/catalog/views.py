from django.db import models
from rest_framework import (
    generics,
    viewsets,
    mixins,
    filters,
    permissions,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from shortage.apps.blog.models import ShortageBlogPost
from shortage.apps.blog.serializers import ShortageBlogPostSlugSerializer
from .models import (
    Organization,
    ExternalOrganization,
    Instruction,
    Product,
    OrganizationBlogPost,
)
from .serializers import (
    OrganizationPreviewSerializer,
    ExternalOrganizationPreviewSerializer,
    InstructionSerializer,
    ProductPreviewWithOrganizationSerializer,
    ProductPreviewSerializer,
    CampaignPreviewSerializer,
    CampaignSerializer,
    OrganizationBlogPostPreviewSerializer,
    OrganizationBlogPostSerializer,
    OrganizationBlogPostSlugSerializer,
    CategorySerializer,
    OrganizationSerializer,
    OrganizationSlugSerializer,
    ProductSerializer,
    OrganizationProductSlugSerializer,
    OrganizationRegistrationRequestSerializer,
)


class PromotedOrganizationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted organizations"""

    queryset = Organization.objects.promoted().order_by("-created_at")
    serializer_class = OrganizationPreviewSerializer


class PromotedExternalOrganizationsViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """A list of promoted external organizations"""

    queryset = ExternalOrganization.objects.order_by("position", "-created_at")
    serializer_class = ExternalOrganizationPreviewSerializer
    paginator = None


class PromotedProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of promoted products"""

    serializer_class = ProductPreviewWithOrganizationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        queryset = Product.objects.promoted().prefetch_related("organization")

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


class PromotedOrganizationBlogPostsViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """A list of promoted blog posts"""

    serializer_class = OrganizationBlogPostPreviewSerializer
    queryset = (
        OrganizationBlogPost.objects.promoted()
        .order_by("-updated_at")
        .prefetch_related("organization")
    )


class OrganizationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Returns information about specific organization if that organization was verified"""

    schema = AutoSchema(
        tags=["Organizations"],
    )

    serializer_class = OrganizationSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Organization.objects.published_or_owned(user=self.request.user)


class InstructionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of instructions that belong to the given organization"""

    serializer_class = InstructionSerializer
    paginator = None

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        return Instruction.objects.filter(organization=organization)


class ProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of public products that belong to the given organization"""

    serializer_class = ProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-top_priority", "position", "-created_at"]

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        queryset = Product.objects.public().filter(organization=organization)

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class CampaignsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of campaigns that belong to the given organization"""

    serializer_class = CampaignPreviewSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        # show only public campaigns on the organization's page
        return (
            organization.campaigns.published_or_owned(user=self.request.user)
            .filter(is_public=True)
            .order_by("-created_at")
        )


class CampaignViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Get campaign by slug, uuid, and organization slug"""

    serializer_class = CampaignSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        # make sure we check by slug and uuid (lookup_field),
        # so private campaigns remain private
        return organization.campaigns.published_or_owned(user=self.request.user).filter(
            slug=self.kwargs["campaign_slug"]
        )


class CampaignCategoriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of categories of the given organization campaign's products"""

    serializer_class = CategorySerializer
    paginator = None

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        campaign = generics.get_object_or_404(
            organization.campaigns.published_or_owned(user=self.request.user),
            organization__slug=self.kwargs["org_slug"],
            slug=self.kwargs["campaign_slug"],
            pk=self.kwargs["campaign_uuid"],
        )
        return (
            campaign.products.active()
            .distinct("category")
            .values_list("category", flat=True)
        )


class CampaignProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A list of campaign products that belong to the given organization"""

    serializer_class = ProductPreviewSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["-top_priority", "position", "-created_at"]

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        campaign = generics.get_object_or_404(
            organization.campaigns.published_or_owned(user=self.request.user),
            organization__slug=self.kwargs["org_slug"],
            slug=self.kwargs["campaign_slug"],
            pk=self.kwargs["campaign_uuid"],
        )
        queryset = campaign.products.active()

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class CampaignProductViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Product details for the given slug and the given organization and campaign"""

    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        self.organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        self.campaign = generics.get_object_or_404(
            self.organization.campaigns.published_or_owned(user=self.request.user),
            organization__slug=self.kwargs["org_slug"],
            slug=self.kwargs["campaign_slug"],
            pk=self.kwargs["campaign_uuid"],
        )
        return self.campaign.products.active()


class OrganizationBlogPostsViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """A list of blog posts that belong to the given organization"""

    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return OrganizationBlogPostPreviewSerializer
        return OrganizationBlogPostSerializer

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        queryset = organization.blog_posts.published_or_owned(
            user=self.request.user
        ).order_by("-updated_at")
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
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
        )
        return (
            Product.objects.public()
            .filter(organization=organization)
            .distinct("category")
            .values_list("category", flat=True)
        )


class ProductViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Product details for the given slug and the given organization"""

    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        organization = generics.get_object_or_404(
            Organization.objects.published_or_owned(user=self.request.user),
            slug=self.kwargs["org_slug"],
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
    """Fetch entities for sitemap"""

    permission_classes = [permissions.AllowAny]

    @action(detail=False)
    def all_organization_slugs(self, request, *args, **kwargs):
        """Get slugs of published organizations"""
        queryset = Organization.objects.published()
        serializer = OrganizationSlugSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def all_product_slugs(self, request, *args, **kwargs):
        """Get slugs of public products of published organizations"""
        queryset = (
            Product.objects.public()
            .filter(
                organization_id__in=models.Subquery(
                    Organization.objects.published().values("id")
                )
            )
            .prefetch_related("organization")
        )
        serializer = OrganizationProductSlugSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def all_blog_post_slugs(self, request, *args, **kwargs):
        """Get slugs of published blog posts of published organizations"""
        queryset = (
            OrganizationBlogPost.objects.published()
            .filter(
                organization_id__in=models.Subquery(
                    Organization.objects.published().values("id")
                )
            )
            .prefetch_related("organization")
        )
        serializer = OrganizationBlogPostSlugSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def all_shortage_blog_post_slugs(self, request, *args, **kwargs):
        """Get slugs of published blog posts from the Shortage Team"""
        queryset = ShortageBlogPost.objects.published()
        serializer = ShortageBlogPostSlugSerializer(queryset, many=True)
        return Response(serializer.data)


class AvailableOrganizationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A list of all available organizations.
    Used by integrations like Shopify
    """

    queryset = Organization.objects.published().order_by("-created_at")
    serializer_class = OrganizationPreviewSerializer


class AvailableProductsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A list of all available products.
    Used by integrations like Shopify
    """

    serializer_class = ProductPreviewWithOrganizationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        queryset = (
            Product.objects.public()
            .filter(
                organization_id__in=models.Subquery(
                    Organization.objects.published().values("id")
                )
            )
            .prefetch_related("organization")
        )

        # filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset
