from rest_framework import generics, permissions
from rest_framework.schemas.openapi import AutoSchema
from .serializers import RegistrationSerializer, ActivationSerializer, ProfileSerializer
from .models import Profile


class RegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistrationSerializer


class ActivationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ActivationSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    schema = AutoSchema(
        tags=["Profiles"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    http_method_names = ["get", "put", "head", "options"]

    def get_object(self):
        obj = generics.get_object_or_404(
            Profile.objects.prefetch_related("user"),
            user=self.request.user,
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
