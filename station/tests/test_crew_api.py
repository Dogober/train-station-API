from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from station.models import Crew
from station.serializers import CrewSerializer

CREW_URL = reverse("station:crew-list")


def sample_crew(**params):
    defaults = {
        "first_name": "First",
        "last_name": "Last",
        "position": "position"
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def detail_url(crew_id):
    return reverse("station:crew-detail", args=[crew_id])


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "test_password",
        )
        self.client.force_authenticate(self.user)

    def test_list_crew(self):
        sample_crew()
        sample_crew(
            first_name="Jon",
            last_name="Doe",
        )

        res = self.client.get(CREW_URL)

        crew = Crew.objects.order_by("first_name")
        serializer = CrewSerializer(crew, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_crew_by_first_name_or_last_name(self):
        crew1 = sample_crew()
        crew2 = sample_crew(
            first_name="Jon",
            last_name="Doe",
        )

        res = self.client.get(
            CREW_URL, {"name_query": "Jon"}
        )

        serializer1 = CrewSerializer(crew1)
        serializer2 = CrewSerializer(crew2)

        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])

    def test_retrieve_crew_detail(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        res = self.client.get(url)

        serializer = CrewSerializer(crew)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "First",
            "last_name": "Last",
            "position": "position"
        }
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_station(self):
        payload = {
            "first_name": "First",
            "last_name": "Last",
            "position": "position"
        }
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        crew = Crew.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(crew, key))
