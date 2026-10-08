from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Shipment, Manifest, Tracking, PickupOrder


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ('resi_number', 'client', 'sender_name', 'receiver_name', 'origin', 'destination', 'service_type', 'display_status', 'created_at')
    list_filter = ('status', 'service_type', 'payment_type', 'created_at')
    search_fields = ('resi_number', 'sender_name', 'receiver_name', 'origin', 'destination', 'client__name')
    list_select_related = ('client', 'contract', 'quotation')

    @display(description="Status Pengiriman", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(Manifest)
class ManifestAdmin(ModelAdmin):
    list_display = ('manifest_number', 'manifest_type', 'driver', 'date', 'display_status')
    list_filter = ('status', 'manifest_type', 'date')
    search_fields = ('manifest_number', 'driver__first_name', 'driver__username')

    @display(description="Status", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(Tracking)
class TrackingAdmin(ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__resi_number', 'location')


@admin.register(PickupOrder)
class PickupOrderAdmin(ModelAdmin):
    list_display = ('pickup_number', 'client', 'pickup_date', 'display_status', 'city', 'district')
    list_filter = ('status', 'pickup_date')
    search_fields = ('pickup_number', 'client__name', 'city', 'district')

    @display(description="Status Pickup", label=True)
    def display_status(self, obj):
        return obj.get_status_display()
