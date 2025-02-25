from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import TrainType
from station.serializers import TrainTypeSerializer

TRAIN_TYPE_URL = reverse("station:traintype-list")


def sample_train_type(**params):
    defaults = {
        "name": "Passenger",
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def detail_url(train_type_id):
    return reverse("station:traintype-detail", args=[train_type_id])


class UnauthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)

    def test_list_train_types(self):
        sample_train_type()
        sample_train_type(
            name="Commuter",
        )

        res = self.client.get(TRAIN_TYPE_URL)

        train_types = TrainType.objects.order_by("name")
        serializer = TrainTypeSerializer(train_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_train_types_by_name(self):
        train_type1 = sample_train_type()
        train_type2 = sample_train_type(
            name="Commuter",
        )

        res = self.client.get(TRAIN_TYPE_URL, {"name": "Passenger"})

        serializer1 = TrainTypeSerializer(train_type1)
        serializer2 = TrainTypeSerializer(train_type2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_train_type_detail(self):
        train_type = sample_train_type()

        url = detail_url(train_type.id)
        res = self.client.get(url)

        serializer = TrainTypeSerializer(train_type)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_type_forbidden(self):
        payload = {"name": "Passenger"}
        res = self.client.post(TRAIN_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train_type(self):
        payload = {"name": "Passenger"}
        res = self.client.post(TRAIN_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train_type = TrainType.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(train_type, key))
