from drf_spectacular.utils import extend_schema, OpenApiParameter
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "method",
                type=str,
                description="Optional filter to search API usage "
                            "logs by HTTP method (e.g., GET, POST). "
                            "This parameter allows you to retrieve logs "
                            "for requests made with the specified HTTP method.",
                required=False,
            ),
            OpenApiParameter(
                "status",
                type=int,
                description="Optional filter to search API usage logs "
                            "by response status code. "
                            "You can provide specific status codes "
                            "to filter the logs accordingly.",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
