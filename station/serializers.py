from django.db import transaction
from rest_framework import serializers

from station.models import (
    Route,
    Station,
    Crew,
    Train,
    TrainType,
    Journey,
    Ticket,
    Order,
    APIUsage,
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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = "__all__"


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "places_in_cargo", "train_type", )


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = "__all__"


class TrainListSerializer(serializers.ModelSerializer):
    train_type = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True
    )
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "image",
            "cargo_num",
            "places_in_cargo",
            "capacity",
            "train_type",
        )


class TrainRetrieveSerializer(serializers.ModelSerializer):
    train_type = TrainTypeSerializer(read_only=True)
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "image",
            "cargo_num",
            "places_in_cargo",
            "capacity",
            "train_type",
        )


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = "__all__"


class JourneyListSerializer(serializers.ModelSerializer):
    route = serializers.StringRelatedField(read_only=True)
    train = serializers.StringRelatedField(read_only=True)
    train_image = serializers.ImageField(
        source="train.image",
        read_only=True
    )
    available_places = serializers.IntegerField(read_only=True)
    crew = serializers.SlugRelatedField(
        slug_field="full_name",
        many=True,
        read_only=True
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "train_image",
            "available_places",
            "crew",
            "departure_time",
            "arrival_time"
        )


class JourneyRetrieveSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(read_only=True)
    train = TrainListSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = serializers.StringRelatedField(
        many=True,
        read_only=True,
        source="tickets"
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "taken_places",
            "crew"
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "cargo", "place", "journey")

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["place"],
            attrs["journey"].train,
            serializers.ValidationError
        )
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False,
        read_only=False
    )

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class APIUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIUsage
        fields = "__all__"
