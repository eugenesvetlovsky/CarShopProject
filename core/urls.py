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
    path('seller/<int:seller_id>/review/<int:order_id>/', views.add_review, name='add_review'),
    path('review/edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    # Личный профиль пользователя
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Чаты и сообщения
    path('chats/', views.chats_list, name='chats_list'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chat/start/<int:seller_id>/<int:car_id>/', views.start_chat, name='start_chat'),
]