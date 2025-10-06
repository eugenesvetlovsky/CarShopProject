from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorite/toggle/<int:car_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # Корзина и заказы
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:car_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:car_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Управление объявлениями
    path('my-listings/', views.my_listings, name='my_listings'),
    path('car/add/', views.add_car, name='add_car'),
    path('car/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('car/delete/<int:car_id>/', views.delete_car, name='delete_car'),
    
    # Профиль продавца и отзывы
    path('seller/<int:user_id>/', views.seller_profile, name='seller_profile'),
    path('seller/<int:seller_id>/review/', views.add_review, name='add_review'),
]