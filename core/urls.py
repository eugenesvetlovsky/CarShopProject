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
]