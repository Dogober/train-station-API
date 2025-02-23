from rest_framework import viewsets
from rest_framework.response import Response
from django.http import HttpRequest

from station.models import APIUsage


class APILoggingMixin(viewsets.ModelViewSet):
    @staticmethod
    def log_request(request: HttpRequest, response: Response) -> None:
        APIUsage.objects.create(
            endpoint=request.build_absolute_uri(),
            method=request.method,
            response_status=response.status_code,
            user_ip=request.META.get("REMOTE_ADDR")
        )

    def create(self, request: HttpRequest, *args, **kwargs) -> Response:
        response = super().create(request, *args, **kwargs)
        self.log_request(request, response)
        return response

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> Response:
        response = super().retrieve(request, *args, **kwargs)
        self.log_request(request, response)
        return response

    def list(self, request: HttpRequest, *args, **kwargs) -> Response:
        response = super().list(request, *args, **kwargs)
        self.log_request(request, response)
        return response
