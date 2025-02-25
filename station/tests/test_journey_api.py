from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import Station, Route, TrainType, Crew, Train, Journey
from station.serializers import JourneyListSerializer, JourneyRetrieveSerializer

JOURNEY_URL = reverse("station:journey-list")


def sample_train_type(**params):
    defaults = {
        "name": "High-Speed"
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)

def sample_crew(**params):
    defaults = {
        "first_name": "First",
        "last_name": "Last",
        "position": "position"
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)

def sample_station(**params):
    defaults = {
        "name": "Kyiv Central Station",
        "longitude": 100.001,
        "latitude": 101.001
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def detail_url(journey_id):
    return reverse("station:journey-detail", args=[journey_id])


class UnauthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(JOURNEY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)
        self.high_speed = sample_train_type()
        self.train = Train.objects.create(
            name="Night Train (Kyiv to Lviv))",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.high_speed,
        )
        self.station_from = sample_station()
        self.station_to = sample_station(
            name="Lviv Podzamche",
            longitude=50.001,
            latitude=51.001
        )
        self.route = Route.objects.create(
            source=self.station_from,
            destination=self.station_to,
            distance_km=500
        )
        self.crew = sample_crew()
        self.journey1 = Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time="2025-03-15T14:30:00Z",
            arrival_time="2025-04-15T14:30:00Z",
        )
        self.journey2 = Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time="2025-05-15T14:30:00Z",
            arrival_time="2025-06-15T14:30:00Z",
        )


    def test_list_journeys(self):
        self.journey1.crew.add(self.crew)
        self.journey2.crew.add(self.crew)

        res = self.client.get(JOURNEY_URL)

        journeys = Journey.objects.annotate(
            available_places=F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets")
        ).order_by("-departure_time")

        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_retrieve_journey_detail(self):
        url = detail_url(self.journey1.id)
        res = self.client.get(url)

        serializer = JourneyRetrieveSerializer(self.journey1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_journeys_by_date(self):
        res = self.client.get(
            JOURNEY_URL, {"date": "2025-05-15"}
        )
        journeys = Journey.objects.annotate(
            available_places=F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets")
        ).order_by("-departure_time")

        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for journey_data in res.data["results"]:
            self.assertIn(journey_data, serializer.data)


    def test_create_journey_forbidden(self):
        payload = {
            "route": self.route.pk,
            "train": self.train.pk,
            "departure_time": "2025-07-15T14:30:00Z",
            "arrival_time": "2025-08-15T14:30:00Z",
            "crew": [self.crew.id]
        }
        res = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_journey(self):
        high_speed = sample_train_type(name="Speed")
        train = Train.objects.create(
            name="Intercity",
            cargo_num=10,
            places_in_cargo=50,
            train_type=high_speed,
        )
        station_from = sample_station(name="Dnipro")
        station_to = sample_station(
            name="Lviv Central",
            longitude=50.001,
            latitude=51.001
        )
        route = Route.objects.create(
            source=station_from,
            destination=station_to,
            distance_km=500
        )
        crew = sample_crew()

        payload = {
            "route": route.pk,
            "train": train.pk,
            "departure_time": "2025-03-15T14:30:00Z",
            "arrival_time": "2025-04-15T14:30:00Z",
            "crew": [crew.id]
        }

        res = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        journey = Journey.objects.get(id=res.data["id"])

        self.assertEqual(payload["route"], journey.route.id)
        self.assertEqual(payload["train"], journey.train.id)
        self.assertEqual(payload["departure_time"], journey.departure_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z")
        self.assertEqual(payload["arrival_time"], journey.arrival_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z")
        self.assertEqual(list(journey.crew.values_list('id', flat=True)), payload["crew"])
