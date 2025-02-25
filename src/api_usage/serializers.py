from rest_framework import serializers

from api_usage.models import APIUsage


class APIUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIUsage
        fields = "__all__"
