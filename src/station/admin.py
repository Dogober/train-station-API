from django.contrib import admin

from station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Crew,
    Order,
    Ticket,
)

admin.site.register(Station)
admin.site.register(Route)
admin.site.register(TrainType)
admin.site.register(Train)
admin.site.register(Crew)
admin.site.register(Journey)


class TicketInline(admin.TabularInline):  # Или StackedInline
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [TicketInline]
