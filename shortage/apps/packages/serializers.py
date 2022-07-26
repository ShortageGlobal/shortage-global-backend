from rest_framework import serializers
from .models import Package


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "delivery_company",
            "tracking_code",
            "created_at",
            "status",
        ]
