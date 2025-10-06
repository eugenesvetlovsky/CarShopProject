from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from .models import Car, Favorite, Cart, Order, Review, UserProfile
from .forms import RegisterForm, LoginForm, CarForm, ReviewForm


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
    
    # Получаем информацию о продавце
    seller_profile = None
    seller_rating = None
    if car.seller:
        seller_profile, created = UserProfile.objects.get_or_create(user=car.seller)
        seller_rating = seller_profile.get_average_rating()
    
    return render(request, 'core/car_detail.html', {
        'car': car,
        'is_favorite': is_favorite,
        'seller_profile': seller_profile,
        'seller_rating': seller_rating,
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


# Управление объявлениями пользователя
@login_required
def my_listings(request):
    """Мои объявления о продаже автомобилей"""
    listings = Car.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'core/my_listings.html', {'listings': listings})


@login_required
def add_car(request):
    """Добавить автомобиль на продажу"""
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.seller = request.user
            car.available = True
            car.save()
            messages.success(request, 'Автомобиль успешно добавлен на продажу!')
            return redirect('core:my_listings')
    else:
        form = CarForm()
    
    return render(request, 'core/add_car.html', {'form': form})


@login_required
def edit_car(request, car_id):
    """Редактировать объявление"""
    car = get_object_or_404(Car, id=car_id, seller=request.user)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('core:my_listings')
    else:
        form = CarForm(instance=car)
    
    return render(request, 'core/edit_car.html', {'form': form, 'car': car})


@login_required
def delete_car(request, car_id):
    """Удалить объявление"""
    car = get_object_or_404(Car, id=car_id, seller=request.user)
    
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Объявление успешно удалено!')
        return redirect('core:my_listings')
    
    return render(request, 'core/delete_car_confirm.html', {'car': car})


# Профиль продавца и отзывы
def seller_profile(request, user_id):
    """Профиль продавца"""
    seller = get_object_or_404(User, id=user_id)
    
    # Создаем профиль если его нет
    profile, created = UserProfile.objects.get_or_create(user=seller)
    
    # Получаем статистику
    cars_for_sale = Car.objects.filter(seller=seller, available=True)
    reviews = Review.objects.filter(seller=seller).select_related('buyer')
    
    # Проверяем, может ли текущий пользователь оставить отзыв
    can_review = False
    if request.user.is_authenticated and request.user != seller:
        # Пользователь может оставить отзыв, если купил хотя бы один автомобиль у этого продавца
        has_purchased = Order.objects.filter(
            user=request.user,
            car__seller=seller,
            status='completed'
        ).exists()
        
        # И еще не оставлял отзыв
        has_reviewed = Review.objects.filter(seller=seller, buyer=request.user).exists()
        
        can_review = has_purchased and not has_reviewed
    
    context = {
        'seller': seller,
        'profile': profile,
        'cars_for_sale': cars_for_sale,
        'reviews': reviews,
        'can_review': can_review,
        'average_rating': profile.get_average_rating(),
        'reviews_count': profile.get_reviews_count(),
        'sales_count': profile.get_sales_count(),
    }
    
    return render(request, 'core/seller_profile.html', context)


@login_required
def add_review(request, seller_id):
    """Добавить отзыв продавцу"""
    seller = get_object_or_404(User, id=seller_id)
    
    # Проверки
    if request.user == seller:
        messages.error(request, 'Вы не можете оставить отзыв самому себе')
        return redirect('core:seller_profile', user_id=seller_id)
    
    # Проверяем, покупал ли пользователь у этого продавца
    has_purchased = Order.objects.filter(
        user=request.user,
        car__seller=seller,
        status='completed'
    ).exists()
    
    if not has_purchased:
        messages.error(request, 'Вы можете оставить отзыв только после покупки автомобиля у этого продавца')
        return redirect('core:seller_profile', user_id=seller_id)
    
    # Проверяем, не оставлял ли уже отзыв
    if Review.objects.filter(seller=seller, buyer=request.user).exists():
        messages.error(request, 'Вы уже оставили отзыв этому продавцу')
        return redirect('core:seller_profile', user_id=seller_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.seller = seller
            review.buyer = request.user
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('core:seller_profile', user_id=seller_id)
    else:
        form = ReviewForm()
    
    return render(request, 'core/add_review.html', {'form': form, 'seller': seller})
