from .serializers import RegistrationSerializer, ActivationSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny


class RegistrationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer


class ActivationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ActivationSerializer
