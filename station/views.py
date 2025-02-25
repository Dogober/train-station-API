from django.db.models import F, Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import APILoggingMixin
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
    TrainImageSerializer,
)


class StationViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                description="Optional filter to search for "
                            "station by name.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouterRetrieveSerializer
        return RouteSerializer


class CrewViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_queryset(self):
        queryset = self.queryset
        name_query = self.request.query_params.get("name_query")
        if name_query:
            queryset = queryset.filter(
                Q(first_name__icontains=name_query) | Q(last_name__icontains=name_query)
            )
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name_query",
                type=str,
                description="Optional filter to search for crew members "
                            "by their first or last name. "
                            "This parameter allows you to find crew members "
                            "whose names contain the "
                            "provided search term, regardless of case sensitivity.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TrainTypeViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                description="Optional filter to search for "
                            "train type by name.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TrainViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Train.objects.all().prefetch_related("train_type")

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainRetrieveSerializer
        if self.action == "upload_image":
            return TrainImageSerializer
        return TrainSerializer

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        types_ids = self.request.query_params.get("types")
        if types_ids:
            types_ids = self._params_to_ints(types_ids)
            queryset = queryset.filter(train_type__in=types_ids)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "types",
                type=str,
                description="Comma-separated list of train "
                            "type IDs to filter journeys. "
                            "This parameter allows you to retrieve "
                            "journeys that are associated "
                            "with the specified train types, enabling "
                            "targeted searches based on type.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class JourneyViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Journey.objects.all().select_related(
        "train",
        "route__source",
        "route__destination"
    ).prefetch_related("crew")

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyRetrieveSerializer
        return JourneySerializer

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date")
        if self.action == "list":
            queryset = queryset.annotate(
                available_places=F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets")
            )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("tickets")
        if date:
            queryset = queryset.filter(
                departure_time__date=date
            )

        return queryset.order_by("-departure_time")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date",
                type=str,
                description="Optional filter to retrieve journeys "
                            "based on the specified departure date. "
                            "The date should be provided in the format YYYY-MM-DD. "
                            "If provided, only journeys with a departure "
                            "time matching this date will be returned.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(APILoggingMixin, viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.prefetch_related("tickets").filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
