from django.contrib import admin

from station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Crew,
    Order,
    Ticket
)

admin.site.register(Station)
admin.site.register(Route)
admin.site.register(TrainType)
admin.site.register(Train)
admin.site.register(Crew)
admin.site.register(Journey)
admin.site.register(Order)
admin.site.register(Ticket)
