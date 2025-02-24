from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser

from api_usage.models import APIUsage
from api_usage.serializers import APIUsageSerializer


class APIUsageViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = APIUsage.objects.all()
    serializer_class = APIUsageSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = self.queryset
        method = self.request.query_params.get("method")
        response_status = self.request.query_params.get("status")

        if method:
            queryset = queryset.filter(method__icontains=method)
        if response_status:
            queryset = queryset.filter(response_status__icontains=response_status)

        return queryset.distinct()
