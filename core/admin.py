from django.contrib import admin
from .models import Car, Order

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'price', 'available')
    list_filter = ('brand', 'year', 'available',)
    search_fields = ('brand', 'model', 'description')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'car', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user_username', 'car_brand', 'car_model')


