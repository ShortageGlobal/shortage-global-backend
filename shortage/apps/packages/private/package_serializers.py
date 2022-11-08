from rest_framework import serializers

from shortage.apps.packages.models import Package


class PrivatePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "uuid",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "delivery_company",
            "tracking_code",
            "note",
            "status",
            "photo",
            "type",
            "created_at",
        ]
        read_only_fields = fields
