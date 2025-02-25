import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Train, TrainType
from station.serializers import TrainListSerializer, TrainRetrieveSerializer

TRAIN_URL = reverse("station:train-list")


def sample_train_type(**params):
    defaults = {"name": "High-Speed"}
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for recipe image upload"""
    return reverse("station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("station:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)
        self.high_speed = sample_train_type()
        self.intercity = sample_train_type(name="Intercity")
        self.passenger = sample_train_type(name="Passenger")

    def test_list_trains(self):
        Train.objects.create(
            name="Night Train (Kyiv to Lviv))",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.high_speed,
        )
        Train.objects.create(
            name="Intercity+",
            cargo_num=8,
            places_in_cargo=50,
            train_type=self.intercity,
        )

        res = self.client.get(TRAIN_URL)

        trains = Train.objects.order_by("cargo_num")
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_trains_by_train_types(self):
        train1 = Train.objects.create(
            name="Night Train (Kyiv to Lviv))",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.high_speed,
        )
        train2 = Train.objects.create(
            name="Intercity+",
            cargo_num=8,
            places_in_cargo=50,
            train_type=self.intercity,
        )
        train3 = Train.objects.create(
            name="Ukrzaliznytsia Passenger",
            cargo_num=10,
            places_in_cargo=60,
            train_type=self.passenger,
        )

        res = self.client.get(
            TRAIN_URL, {"types": f"{self.high_speed.id},{self.intercity.id}"}
        )

        serializer1 = TrainListSerializer(train1)
        serializer2 = TrainListSerializer(train2)
        serializer3 = TrainListSerializer(train3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_train_detail(self):
        train = Train.objects.create(
            name="Night Train (Kyiv to Lviv))",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.high_speed,
        )

        url = detail_url(train.id)
        res = self.client.get(url)

        serializer = TrainRetrieveSerializer(train)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "Night Train (Kyiv to Lviv))",
            "cargo_num": 10,
            "places_in_cargo": 50,
            "train_type": self.high_speed,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.high_speed = sample_train_type()

    def test_create_train(self):
        payload = {
            "name": "Night Train (Kyiv to Lviv))",
            "cargo_num": 10,
            "places_in_cargo": 50,
            "train_type": self.high_speed.id,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        train = Train.objects.get(id=res.data["id"])

        self.assertEqual(payload["name"], train.name)
        self.assertEqual(payload["cargo_num"], train.cargo_num)
        self.assertEqual(payload["places_in_cargo"], train.places_in_cargo)
        self.assertEqual(payload["train_type"], train.train_type.id)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.train_type = sample_train_type()
        self.train = Train.objects.create(
            name="Night Train (Kyiv to Lviv))",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type,
        )

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to movie"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list_should_not_work(self):
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Intercity+",
                    "cargo_num": 8,
                    "places_in_cargo": 50,
                    "train_type": self.train_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Night Train (Kyiv to Lviv))")
        self.assertFalse(train.image)
