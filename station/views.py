from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from station.models import (
    Station,
    Route,
    Crew,
    TrainType,
    Train,
    Journey,
    Order,
)
from station.serializers import (
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouterRetrieveSerializer,
    CrewSerializer,
    TrainTypeSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    TrainSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyRetrieveSerializer,
    OrderSerializer,
)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().prefetch_related("source", "destination")

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouterRetrieveSerializer
        return RouteSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all().prefetch_related("train_type")

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainRetrieveSerializer
        return TrainSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyRetrieveSerializer
        return JourneySerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.prefetch_related(
                "route", "train", "crew"
            ).annotate(
                available_places=F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets")
            )
        if self.action == "retrieve":
            return self.queryset.prefetch_related(
                "route", "train", "crew", "tickets"
            )
        return self.queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
