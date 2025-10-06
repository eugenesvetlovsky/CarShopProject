from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Car, Favorite, Cart, Order
from .forms import RegisterForm, LoginForm


def car_list(request):
    cars = Car.objects.filter(available=True)
    
    # Фильтрация по цене
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    if price_min:
        cars = cars.filter(price__gte=price_min)
    if price_max:
        cars = cars.filter(price__lte=price_max)
    
    # Фильтрация по году
    year_min = request.GET.get('year_min')
    year_max = request.GET.get('year_max')
    
    if year_min:
        cars = cars.filter(year__gte=year_min)
    if year_max:
        cars = cars.filter(year__lte=year_max)
    
    # Фильтрация по марке
    brand = request.GET.get('brand')
    if brand:
        cars = cars.filter(brand__icontains=brand)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    cars = cars.order_by(sort_by)
    
    # Получаем список ID избранных автомобилей для текущего пользователя
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('car_id', flat=True)
    
    # Получаем уникальные марки для фильтра (только доступные автомобили)
    brands = Car.objects.filter(available=True).values_list('brand', flat=True).distinct().order_by('brand')
    
    context = {
        'cars': cars,
        'favorite_ids': list(favorite_ids),
        'brands': brands,
        'filters': {
            'price_min': price_min or '',
            'price_max': price_max or '',
            'year_min': year_min or '',
            'year_max': year_max or '',
            'brand': brand or '',
            'sort': sort_by,
        }
    }
    
    return render(request, 'core/car_list.html', context)


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


@login_required
def add_to_cart(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    # Проверяем доступность автомобиля
    if not car.available:
        messages.error(request, 'Этот автомобиль уже недоступен для покупки')
        return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))
    
    # Добавляем в корзину или сообщаем, что уже есть
    cart_item, created = Cart.objects.get_or_create(user=request.user, car=car)
    
    if created:
        messages.success(request, f'{car.brand} {car.model} добавлен в корзину')
    else:
        messages.info(request, 'Этот автомобиль уже в вашей корзине')
    
    return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('car')
    
    # Вычисляем общую стоимость
    total_price = sum(item.car.price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    
    return render(request, 'core/cart.html', context)


@login_required
def remove_from_cart(request, car_id):
    cart_item = get_object_or_404(Cart, user=request.user, car_id=car_id)
    car_name = f"{cart_item.car.brand} {cart_item.car.model}"
    cart_item.delete()
    
    messages.success(request, f'{car_name} удалён из корзины')
    return redirect('core:cart')


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('car')
    
    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('core:cart')
    
    # Создаём заказы для каждого автомобиля в корзине
    orders = []
    cars_info = []
    
    for cart_item in cart_items:
        car = cart_item.car
        
        # Проверяем доступность
        if not car.available:
            messages.error(request, f'{car.brand} {car.model} больше недоступен')
            continue
        
        # Создаём заказ
        order = Order.objects.create(
            user=request.user,
            car=car,
            status='completed'
        )
        orders.append(order)
        
        # Делаем автомобиль недоступным
        car.available = False
        car.save()
        
        # Сохраняем информацию для письма
        cars_info.append({
            'brand': car.brand,
            'model': car.model,
            'year': car.year,
            'price': car.price,
        })
        
        # Удаляем из корзины
        cart_item.delete()
    
    if not orders:
        messages.error(request, 'Не удалось оформить заказ')
        return redirect('core:cart')
    
    # Отправляем email
    try:
        subject = f'Подтверждение заказа #{orders[0].id} - CarShop'
        
        # HTML версия письма
        html_message = render_to_string('core/email/order_confirmation.html', {
            'user': request.user,
            'cars': cars_info,
            'total_price': sum(car['price'] for car in cars_info),
            'order_id': orders[0].id,
        })
        
        # Текстовая версия письма
        plain_message = f"""
Здравствуйте, {request.user.username}!

Спасибо за ваш заказ в CarShop!

Детали заказа:
"""
        for car in cars_info:
            plain_message += f"\n- {car['brand']} {car['model']} ({car['year']}) - {car['price']} ₽"
        
        plain_message += f"\n\nОбщая стоимость: {sum(car['price'] for car in cars_info)} ₽"
        plain_message += "\n\nС уважением,\nКоманда CarShop"
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        messages.success(request, f'Заказ успешно оформлен! Письмо с подтверждением отправлено на {request.user.email}')
    except Exception as e:
        messages.warning(request, f'Заказ оформлен, но не удалось отправить email: {str(e)}')
    
    return redirect('core:order_success', order_id=orders[0].id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_success.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).select_related('car').order_by('-created_at')
    return render(request, 'core/my_orders.html', {'orders': orders})
