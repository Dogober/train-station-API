from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from common.utils import create_custom_path


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    objects = models.Manager()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="routes_from"
    )
    destination = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="routes_to"
    )
    distance_km = models.PositiveIntegerField()
    objects = models.Manager()

    class Meta:
        ordering = ["distance_km"]

    def __str__(self) -> str:
        return f"{self.source} -> {self.destination}"


class TrainType(models.Model):
    name = models.CharField(max_length=63, unique=True)
    description = models.TextField(null=True, blank=True)
    objects = models.Manager()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=63, unique=True)
    cargo_num = models.PositiveIntegerField()
    places_in_cargo = models.PositiveIntegerField()
    train_type = models.ForeignKey(
        TrainType, on_delete=models.CASCADE, related_name="trains"
    )
    image = models.ImageField(null=True, upload_to=create_custom_path)
    objects = models.Manager()

    class Meta:
        ordering = ["cargo_num"]

    @property
    def capacity(self) -> int:
        return self.cargo_num * self.places_in_cargo

    def __str__(self) -> str:
        return f"'{self.name}' (Capacity: {self.capacity} places)"


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, default="staff")
    objects = models.Manager()

    class Meta:
        ordering = ["first_name"]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return f"{self.full_name} position - {self.position}"


class Journey(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="journeys"
    )
    train = models.ForeignKey(
        Train, on_delete=models.CASCADE, related_name="journeys"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="journeys")
    objects = models.Manager()

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self) -> str:
        return f"Route: {self.route} at {self.departure_time}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Created at {self.created_at}"


class Ticket(models.Model):
    cargo = models.PositiveIntegerField()
    place = models.PositiveIntegerField()
    journey = models.ForeignKey(
        Journey, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )
    objects = models.Manager()

    class Meta:
        unique_together = ("journey", "cargo", "place")
        ordering = ["cargo", "place"]

    @staticmethod
    def validate_ticket(cargo, place, journey, error_to_raise):
        for ticket_attr_value, ticket_attr_name, journey_attr_name in [
            (cargo, "cargo", "cargo_num"),
            (place, "place", "places_in_cargo"),
        ]:
            count_attrs = getattr(journey, journey_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {journey_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.place,
            self.journey.train,
            ValidationError,
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"Cargo {self.cargo} | Place {self.place}"
