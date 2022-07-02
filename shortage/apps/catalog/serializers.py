from calendar import c
from rest_framework import serializers
from .models import Organization, Instruction, Product, OnlineStore


class OrganizationSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source='medium_photo', read_only=True)
    
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'description', 'photo', 'url', 'is_draft', 'is_validated']
        
        
class ProductSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source='medium_photo', read_only=True)
    
    class Meta:
        model = Product
        fields = ['name', 'slug', 'category', 'photo', 'price', 'requested_amount', 'description', 'top_priority', 'position']
    