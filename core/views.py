from django.shortcuts import render, redirect
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
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
    context = AuthService.process_registration(request)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/register.html', context)


def login_view(request):
    context = AuthService.process_login(request)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/login.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('core:car_list')


@login_required
def toggle_favorite(request, car_id):
    context = FavoriteService.process_toggle_favorite(request, car_id)
    if context.get('ajax'):
        return JsonResponse({'is_favorite': context['is_favorite'], 'message': context['message']})
    return redirect(request.META.get('HTTP_REFERER', 'core:car_list'))


@login_required
def favorites_view(request):
    """Избранное"""
    context = FavoriteService.get_favorites_context(request)
    return render(request, 'core/favorites.html', context)


@login_required
def add_to_cart(request, car_id):
    CartService.process_add_to_cart(request, car_id)
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
    context = OrderService.process_checkout(request)
    if 'redirect_args' in context:
        return redirect(context['redirect'], order_id=context['redirect_args']['order_id'])
    return redirect(context['redirect'])


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
    context = CarService.process_add_car(request)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/add_car.html', context)


@login_required
def edit_car(request, car_id):
    context = CarService.process_edit_car(request, car_id)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/edit_car.html', context)


@login_required
def delete_car(request, car_id):
    context = CarService.process_delete_car(request, car_id)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/delete_car_confirm.html', context)


# Профиль продавца и отзывы
def seller_profile(request, user_id):
    """Профиль продавца"""
    context = ProfileService.get_seller_profile_context(request, user_id)
    return render(request, 'core/seller_profile.html', context)


@login_required
def add_review(request, seller_id, order_id):
    context = ReviewService.process_add_review(request, seller_id, order_id)
    if 'redirect' in context:
        return redirect(context['redirect'], user_id=context['redirect_args']['user_id'])
    return render(request, 'core/add_review.html', context)


@login_required
def edit_review(request, review_id):
    context = ReviewService.process_edit_review(request, review_id)
    if 'redirect' in context:
        return redirect(context['redirect'], user_id=context['redirect_args']['user_id'])
    return render(request, 'core/edit_review.html', context)


@login_required
def delete_review(request, review_id):
    context = ReviewService.process_delete_review(request, review_id)
    if 'redirect' in context:
        return redirect(context['redirect'], user_id=context['redirect_args']['user_id'])
    return render(request, 'core/delete_review_confirm.html', context)


# Профиль пользователя
@login_required
def my_profile(request):
    """Личный профиль пользователя"""
    context = ProfileService.get_my_profile_context(request)
    return render(request, 'core/my_profile.html', context)


@login_required
def edit_profile(request):
    context = ProfileService.process_edit_profile(request)
    return redirect(context['redirect']) if 'redirect' in context else render(request, 'core/edit_profile.html', context)


@login_required
def change_password(request):
    context = ProfileService.process_change_password(request)
    if 'redirect' in context:
        if context.get('update_session'):
            update_session_auth_hash(request, request.user)
        return redirect(context['redirect'])
    return render(request, 'core/change_password.html', context)


# Система сообщений
@login_required
def chats_list(request):
    """Список всех чатов пользователя"""
    context = ChatService.get_chats_list_context(request)
    return render(request, 'core/chats_list.html', context)


@login_required
def chat_detail(request, chat_id):
    context = ChatService.process_chat_detail(request, chat_id)
    if 'redirect' in context:
        if 'redirect_args' in context:
            return redirect(context['redirect'], chat_id=context['redirect_args']['chat_id'])
        return redirect(context['redirect'])
    return render(request, 'core/chat_detail.html', context)


@login_required
def start_chat(request, seller_id, car_id):
    context = ChatService.process_start_chat(request, seller_id, car_id)
    if 'car_id' in context.get('redirect_args', {}):
        return redirect(context['redirect'], car_id=context['redirect_args']['car_id'])
    return redirect(context['redirect'], chat_id=context['redirect_args']['chat_id'])
