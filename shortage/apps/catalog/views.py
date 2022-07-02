from rest_framework import viewsets
from rest_framework import viewsets
from .models import Organization, Product
from .serializers import OrganizationSerializer, ProductSerializer

default_http_method_names = [
    "get",
    "head",
    "options",
    "trace",
]

# Organizations
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


# Product
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
