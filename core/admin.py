from django.contrib import admin
from .models import Car, Order, Favorite, Cart

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'price', 'available')
    list_filter = ('brand', 'year', 'available',)
    search_fields = ('brand', 'model', 'description')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'car', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'car__brand', 'car__model')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'car__brand', 'car__model')
    readonly_fields = ('created_at',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'car__brand', 'car__model')


