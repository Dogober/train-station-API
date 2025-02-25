from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import Station
from station.serializers import StationSerializer

STATION_URL = reverse("station:station-list")


def sample_station(**params):
    defaults = {
        "name": "Kyiv Central Station",
        "longitude": 100.001,
        "latitude": 101.001
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def detail_url(station_id):
    return reverse("station:station-detail", args=[station_id])


class UnauthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(STATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)

    def test_list_stations(self):
        sample_station()
        sample_station(
            name="Lviv Podzamche",
            longitude=50.001,
            latitude=51.001
        )

        res = self.client.get(STATION_URL)

        stations = Station.objects.order_by("name")
        serializer = StationSerializer(stations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_stations_by_name(self):
        station1 = sample_station()
        station2 = sample_station(
            name="Lviv Podzamche",
            longitude=50.001,
            latitude=51.001
        )

        res = self.client.get(
            STATION_URL, {"name": "Kyiv"}
        )

        serializer1 = StationSerializer(station1)
        serializer2 = StationSerializer(station2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_station_detail(self):
        station = sample_station()

        url = detail_url(station.id)
        res = self.client.get(url)

        serializer = StationSerializer(station)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_station_forbidden(self):
        payload = {
            "name": "Kyiv Central Station",
            "longitude": 100.001,
            "latitude": 101.001
        }
        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_station(self):
        payload = {
            "name": "Kyiv Central Station",
            "longitude": 100.001,
            "latitude": 101.001
        }
        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        station = Station.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(station, key))
