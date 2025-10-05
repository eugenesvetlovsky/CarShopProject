from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Car, Favorite
from .forms import RegisterForm, LoginForm


def car_list(request):
    cars = Car.objects.filter(available=True)
    
    # Получаем список ID избранных автомобилей для текущего пользователя
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('car_id', flat=True)
    
    return render(request, 'core/car_list.html', {
        'cars': cars,
        'favorite_ids': list(favorite_ids)
    })


def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    # Проверяем, добавлен ли автомобиль в избранное
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, car=car).exists()
    
    return render(request, 'core/car_detail.html', {
        'car': car,
        'is_favorite': is_favorite
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:car_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('core:car_list')
    else:
        form = RegisterForm()
    
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:car_list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('core:car_list')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('core:car_list')


@login_required
def toggle_favorite(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, car=car)
    
    if not created:
        favorite.delete()
        is_favorite = False
        message = 'Удалено из избранного'
    else:
        is_favorite = True
        message = 'Добавлено в избранное'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'is_favorite': is_favorite,
            'message': message
        })
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))


@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('car')
    return render(request, 'core/favorites.html', {'favorites': favorites})
