from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.mixins import APILoggingMixin
from user.serializers import UserSerializer


class CreateUserView(APILoggingMixin, generics.CreateAPIView):
    serializer_class = UserSerializer


class ManageUserView(APILoggingMixin, generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
