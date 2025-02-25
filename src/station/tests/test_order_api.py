from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import (
    TrainType,
    Crew,
    Station,
    Train,
    Route,
    Journey,
    Order,
)


ORDER_URL = reverse("station:order-list")


def sample_train_type(**params):
    defaults = {"name": "High-Speed"}
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def sample_crew(**params):
    defaults = {
        "first_name": "First",
        "last_name": "Last",
        "position": "position",
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def sample_station(**params):
    defaults = {
        "name": "Kyiv Central Station",
        "longitude": 100.001,
        "latitude": 101.001,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)

    def test_create_order_with_tickets(self):

        high_speed = sample_train_type(name="Speed")
        train = Train.objects.create(
            name="Intercity",
            cargo_num=10,
            places_in_cargo=50,
            train_type=high_speed,
        )
        station_from = sample_station(name="Dnipro")
        station_to = sample_station(name="Lviv Central")
        route = Route.objects.create(
            source=station_from, destination=station_to, distance_km=500
        )
        crew = sample_crew()
        journey = Journey.objects.create(
            route=route,
            train=train,
            departure_time="2025-03-15T14:30:00Z",
            arrival_time="2025-04-15T14:30:00Z",
        )
        journey.crew.add(crew)

        tickets_data = [
            {"cargo": 1, "place": 2, "journey": journey.id},
            {"cargo": 2, "place": 3, "journey": journey.id},
        ]

        payload = {
            "created_at": datetime.now(),
            "user": self.user.id,
            "tickets": tickets_data,
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.user, self.user)

        self.assertEqual(order.tickets.count(), 2)

    def test_create_order_without_tickets(self):
        payload = {"tickets": []}
        res = self.client.post(ORDER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
