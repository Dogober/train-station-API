from rest_framework import serializers

from station.models import (
    Route,
    Station,
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = "__all__"


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = "__all__"


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
    destination = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )


class RouterRetrieveSerializer(RouteSerializer):
    source = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)
