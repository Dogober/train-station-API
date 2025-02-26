from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import Station, Route
from station.serializers import RouterRetrieveSerializer, RouteListSerializer

ROUTE_URL = reverse("station:route-list")


def sample_station(**params):
    defaults = {
        "name": "Kyiv Central Station",
        "longitude": 100.001,
        "latitude": 101.001,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def detail_url(route_id):
    return reverse("station:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        station_from = sample_station()
        station_to = sample_station(
            name="Lviv Podzamche", longitude=50.001, latitude=51.001
        )
        Route.objects.create(
            source=station_from, destination=station_to, distance_km=500
        )

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("distance_km")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_retrieve_route_detail(self):
        station_from = sample_station()
        station_to = sample_station(
            name="Lviv Podzamche", longitude=50.001, latitude=51.001
        )

        route = Route.objects.create(
            source=station_from, destination=station_to, distance_km=500
        )

        url = detail_url(route.id)
        res = self.client.get(url)

        serializer = RouterRetrieveSerializer(route)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        station_from = sample_station()
        station_to = sample_station(
            name="Lviv Podzamche", longitude=50.001, latitude=51.001
        )
        payload = {
            "source": station_from.pk,
            "destination": station_to.pk,
            "distance_km": 500,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        station_from = sample_station()
        station_to = sample_station(
            name="Lviv Podzamche", longitude=50.001, latitude=51.001
        )
        payload = {
            "source": station_from.pk,
            "destination": station_to.pk,
            "distance_km": 500,
        }

        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        route = Route.objects.get(id=res.data["id"])

        self.assertEqual(payload["source"], route.source.id)
        self.assertEqual(payload["destination"], route.destination.id)
        self.assertEqual(payload["distance_km"], route.distance_km)
