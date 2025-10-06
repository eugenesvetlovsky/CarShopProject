from django.contrib import admin
from .models import Car, Order, Favorite, Cart, Review, UserProfile

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'price', 'seller', 'available')
    list_filter = ('brand', 'year', 'available', 'seller')
    search_fields = ('brand', 'model', 'description')
    readonly_fields = ('created_at', 'updated_at')

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

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('seller', 'buyer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('seller__username', 'buyer__username', 'comment')
    readonly_fields = ('created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_average_rating', 'get_reviews_count', 'get_sales_count')
    search_fields = ('user__username',)


