from django.urls import path, include
from rest_framework import routers

from api_usage.views import APIUsageViewSet


app_name = "api-usage"

router = routers.DefaultRouter()

router.register("", APIUsageViewSet)

urlpatterns = [
    path("", include(router.urls))
]
