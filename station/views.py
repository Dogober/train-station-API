from rest_framework import viewsets

from station.models import (
    Station,
    Route,
)
from station.serializers import (
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouterRetrieveSerializer,
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
