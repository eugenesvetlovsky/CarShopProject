from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Car, Favorite, Cart, Order, Review, UserProfile, Chat, Message
from .forms import RegisterForm, LoginForm, CarForm, ReviewForm, UserUpdateForm, PasswordChangeCustomForm
from .services import (
    CarService, FavoriteService, CartService, OrderService,
    ReviewService, ChatService, ProfileService, AuthService
)


def car_list(request):
    """Список автомобилей с фильтрацией"""
    context = CarService.get_car_list_context(request)
    return render(request, 'core/car_list.html', context)


def car_detail(request, car_id):
    """Детальная информация об автомобиле"""
    context = CarService.get_car_detail_context(request, car_id)
    return render(request, 'core/car_detail.html', context)


def register_view(request):
    """Регистрация пользователя"""
    if request.user.is_authenticated:
        return redirect('core:car_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        success, user, message = AuthService.process_registration(request, form)
        if success:
            login(request, user)
            messages.success(request, message)
            return redirect('core:car_list')
    else:
        form = RegisterForm()
    
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('core:car_list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        success, user, message = AuthService.process_login(request, form)
        if success:
            login(request, user)
            messages.success(request, message)
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
    """Добавить/удалить из избранного"""
    is_favorite, message = FavoriteService.process_toggle_favorite(request, car_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_favorite, 'message': message})
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))


@login_required
def favorites_view(request):
    """Избранное"""
    context = FavoriteService.get_favorites_context(request)
    return render(request, 'core/favorites.html', context)


@login_required
def add_to_cart(request, car_id):
    """Добавить автомобиль в корзину"""
    success, message = CartService.process_add_to_cart(request, car_id)
    
    if success:
        messages.success(request, message)
    else:
        messages.info(request, message)
    
    return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))


@login_required
def cart_view(request):
    """Просмотр корзины"""
    context = CartService.get_cart_context(request)
    return render(request, 'core/cart.html', context)


@login_required
def remove_from_cart(request, car_id):
    """Удалить из корзины"""
    message = CartService.remove_from_cart(request.user, car_id)
    messages.success(request, message)
    return redirect('core:cart')


@login_required
def checkout(request):
    """Оформление заказа"""
    orders, result = OrderService.create_orders_from_cart(request.user)
    
    if not orders:
        messages.warning(request, result)
        return redirect('core:cart')
    
    success, message = OrderService.send_order_confirmation_email(request.user, orders, result)
    
    if success:
        messages.success(request, message)
    else:
        messages.warning(request, message)
    
    return redirect('core:order_success', order_id=orders[0].id)


@login_required
def order_success(request, order_id):
    """Успешное оформление заказа"""
    context = OrderService.get_order_success_context(request, order_id)
    return render(request, 'core/order_success.html', context)


@login_required
def my_orders(request):
    """Мои заказы"""
    context = OrderService.get_my_orders_context(request)
    return render(request, 'core/my_orders.html', context)

# Управление объявлениями пользователя
@login_required
def my_listings(request):
    """Мои объявления о продаже автомобилей"""
    context = CarService.get_my_listings_context(request)
    return render(request, 'core/my_listings.html', {'listings': context['cars']})


@login_required
def add_car(request):
    """Добавить автомобиль на продажу"""
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        success, message = CarService.process_add_car(request, form)
        if success:
            messages.success(request, message)
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
        success, message = CarService.process_edit_car(request, car, form)
        if success:
            messages.success(request, message)
            return redirect('core:my_listings')
    else:
        form = CarForm(instance=car)
    
    return render(request, 'core/edit_car.html', {'form': form, 'car': car})


@login_required
def delete_car(request, car_id):
    """Удалить объявление"""
    car = get_object_or_404(Car, id=car_id, seller=request.user)
    
    if request.method == 'POST':
        message = CarService.process_delete_car(car)
        messages.success(request, message)
        return redirect('core:my_listings')
    
    return render(request, 'core/delete_car_confirm.html', {'car': car})


# Профиль продавца и отзывы
def seller_profile(request, user_id):
    """Профиль продавца"""
    context = ProfileService.get_seller_profile_context(request, user_id)
    return render(request, 'core/seller_profile.html', context)


@login_required
def add_review(request, seller_id, order_id):
    """Добавить отзыв продавцу по конкретному заказу"""
    context = ReviewService.get_add_review_context(request, seller_id, order_id)
    seller = context['seller']
    order = context['order']
    
    can_review, error_message = ReviewService.can_add_review(request.user, seller, order)
    if not can_review:
        messages.error(request, error_message)
        return redirect('core:seller_profile', user_id=seller_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        success, message = ReviewService.process_add_review(request, seller, order, form)
        if success:
            messages.success(request, message)
            return redirect('core:seller_profile', user_id=seller_id)
    else:
        form = ReviewForm()
    
    context['form'] = form
    return render(request, 'core/add_review.html', context)


@login_required
def edit_review(request, review_id):
    """Редактировать свой отзыв"""
    review = get_object_or_404(Review, id=review_id, buyer=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        success, message = ReviewService.process_edit_review(review, form)
        if success:
            messages.success(request, message)
            return redirect('core:seller_profile', user_id=review.seller.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'core/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    """Удалить свой отзыв"""
    review = get_object_or_404(Review, id=review_id, buyer=request.user)
    
    if request.method == 'POST':
        seller_id, message = ReviewService.process_delete_review(review)
        messages.success(request, message)
        return redirect('core:seller_profile', user_id=seller_id)
    
    return render(request, 'core/delete_review_confirm.html', {'review': review})


# Профиль пользователя
@login_required
def my_profile(request):
    """Личный профиль пользователя"""
    context = ProfileService.get_my_profile_context(request)
    return render(request, 'core/my_profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        success, message = ProfileService.process_edit_profile(request, form)
        if success:
            messages.success(request, message)
            return redirect('core:my_profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'core/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.POST)
        success, message = ProfileService.process_change_password(request, form)
        if success:
            update_session_auth_hash(request, request.user)
            messages.success(request, message)
            return redirect('core:my_profile')
        elif message:
            messages.error(request, message)
    else:
        form = PasswordChangeCustomForm()
    
    return render(request, 'core/change_password.html', {'form': form})


# Система сообщений
@login_required
def chats_list(request):
    """Список всех чатов пользователя"""
    context = ChatService.get_chats_list_context(request)
    return render(request, 'core/chats_list.html', context)


@login_required
def chat_detail(request, chat_id):
    """Детальный просмотр чата и отправка сообщений"""
    context = ChatService.get_chat_detail_context(request, chat_id)
    chat = context['chat']
    
    if request.user not in [chat.user1, chat.user2]:
        messages.error(request, 'У вас нет доступа к этому чату')
        return redirect('core:chats_list')
    
    if request.method == 'POST':
        text = request.POST.get('message_text', '').strip()
        if text:
            ChatService.create_message(chat, request.user, text)
            return redirect('core:chat_detail', chat_id=chat.id)
    
    return render(request, 'core/chat_detail.html', context)


@login_required
def start_chat(request, seller_id, car_id):
    """Начать чат с продавцом по конкретному автомобилю"""
    chat, created, message, error_car_id = ChatService.process_start_chat(request, seller_id, car_id)
    
    if chat is None:
        messages.error(request, message)
        return redirect('core:car_detail', car_id=error_car_id)
    
    if message:
        messages.success(request, message)
    
    return redirect('core:chat_detail', chat_id=chat.id)
