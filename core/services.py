"""
Сервисный слой для бизнес-логики приложения.
Содержит функции для работы с моделями, отделенные от представлений.
"""

from django.db.models import Q, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Car, Favorite, Cart, Order, Review, UserProfile, Chat, Message


# ==================== АВТОМОБИЛИ ====================

class CarService:
    """Сервис для работы с автомобилями"""
    
    @staticmethod
    def get_car_list_context(request):
        """Получить контекст для списка автомобилей"""
        filters = {
            'price_min': request.GET.get('price_min'),
            'price_max': request.GET.get('price_max'),
            'year_min': request.GET.get('year_min'),
            'year_max': request.GET.get('year_max'),
            'brand': request.GET.get('brand'),
            'sort': request.GET.get('sort', '-created_at'),
        }
        
        cars = Car.objects.filter(available=True)
        
        # Фильтрация
        if filters.get('price_min'):
            cars = cars.filter(price__gte=filters['price_min'])
        if filters.get('price_max'):
            cars = cars.filter(price__lte=filters['price_max'])
        if filters.get('year_min'):
            cars = cars.filter(year__gte=filters['year_min'])
        if filters.get('year_max'):
            cars = cars.filter(year__lte=filters['year_max'])
        if filters.get('brand'):
            cars = cars.filter(brand__icontains=filters['brand'])
        
        cars = cars.order_by(filters.get('sort', '-created_at'))
        
        favorite_ids = FavoriteService.get_favorite_ids(request.user)
        brands = Car.objects.filter(available=True).values_list('brand', flat=True).distinct().order_by('brand')
        
        return {
            'cars': cars,
            'favorite_ids': favorite_ids,
            'brands': brands,
            'filters': {k: v or '' for k, v in filters.items()}
        }
    
    @staticmethod
    def get_car_detail_context(request, car_id):
        """Получить контекст для детального просмотра автомобиля"""
        car = Car.objects.get(id=car_id)
        is_favorite = FavoriteService.is_favorite(request.user, car)
        
        seller_profile = None
        seller_rating = None
        if car.seller:
            seller_profile, _ = UserProfile.objects.get_or_create(user=car.seller)
            seller_rating = seller_profile.get_average_rating()
        
        return {
            'car': car,
            'is_favorite': is_favorite,
            'seller_profile': seller_profile,
            'seller_rating': seller_rating,
        }
    
    @staticmethod
    def get_my_listings_context(request):
        """Получить контекст моих объявлений"""
        cars = Car.objects.filter(seller=request.user).order_by('-created_at')
        return {'cars': cars}
    
    @staticmethod
    def create_car(user, form_data):
        """Создать автомобиль"""
        car = Car.objects.create(
            seller=user,
            **form_data
        )
        return car
    
    @staticmethod
    def update_car(car, form_data):
        """Обновить автомобиль"""
        for key, value in form_data.items():
            setattr(car, key, value)
        car.save()
        return car
    
    @staticmethod
    def process_add_car(request, form):
        """Обработать добавление автомобиля"""
        if form.is_valid():
            car = form.save(commit=False)
            car.seller = request.user
            car.available = True
            car.save()
            return True, 'Автомобиль успешно добавлен на продажу!'
        return False, None
    
    @staticmethod
    def process_edit_car(request, car, form):
        """Обработать редактирование автомобиля"""
        if form.is_valid():
            form.save()
            return True, 'Объявление успешно обновлено!'
        return False, None
    
    @staticmethod
    def process_delete_car(car):
        """Обработать удаление автомобиля"""
        car.delete()
        return 'Объявление успешно удалено!'


# ==================== ИЗБРАННОЕ ====================

class FavoriteService:
    """Сервис для работы с избранным"""
    
    @staticmethod
    def get_favorite_ids(user):
        """Получить ID избранных автомобилей пользователя"""
        if user.is_authenticated:
            return list(Favorite.objects.filter(user=user).values_list('car_id', flat=True))
        return []
    
    @staticmethod
    def toggle_favorite(user, car):
        """Переключить статус избранного"""
        favorite, created = Favorite.objects.get_or_create(user=user, car=car)
        
        if not created:
            favorite.delete()
            return False, 'Удалено из избранного'
        
        return True, 'Добавлено в избранное'
    
    @staticmethod
    def is_favorite(user, car):
        """Проверить, добавлен ли автомобиль в избранное"""
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, car=car).exists()
        return False
    
    @staticmethod
    def get_favorites_context(request):
        """Получить контекст избранного"""
        favorites = Favorite.objects.filter(user=request.user).select_related('car')
        return {'favorites': favorites}
    
    @staticmethod
    def process_toggle_favorite(request, car_id):
        """Обработать переключение избранного"""
        car = Car.objects.get(id=car_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, car=car)
        
        if not created:
            favorite.delete()
            return False, 'Удалено из избранного'
        
        return True, 'Добавлено в избранное'


# ==================== КОРЗИНА ====================

class CartService:
    """Сервис для работы с корзиной"""
    
    @staticmethod
    def add_to_cart(user, car):
        """Добавить автомобиль в корзину"""
        if not car.available:
            return False, 'Этот автомобиль уже недоступен для покупки'
        
        cart_item, created = Cart.objects.get_or_create(user=user, car=car)
        
        if created:
            return True, f'{car.brand} {car.model} добавлен в корзину'
        
        return False, 'Этот автомобиль уже в вашей корзине'
    
    @staticmethod
    def get_cart_context(request):
        """Получить контекст корзины"""
        cart_items = Cart.objects.filter(user=request.user).select_related('car')
        total_price = sum(item.car.price for item in cart_items)
        
        return {
            'cart_items': cart_items,
            'total_price': total_price,
        }
    
    @staticmethod
    def remove_from_cart(user, car_id):
        """Удалить из корзины"""
        cart_item = Cart.objects.get(user=user, car_id=car_id)
        car_name = f"{cart_item.car.brand} {cart_item.car.model}"
        cart_item.delete()
        return f'{car_name} удалён из корзины'
    
    @staticmethod
    def process_add_to_cart(request, car_id):
        """Обработать добавление в корзину"""
        car = Car.objects.get(id=car_id)
        
        if not car.available:
            return False, 'Этот автомобиль уже недоступен для покупки'
        
        cart_item, created = Cart.objects.get_or_create(user=request.user, car=car)
        
        if created:
            return True, f'{car.brand} {car.model} добавлен в корзину'
        
        return False, 'Этот автомобиль уже в вашей корзине'


# ==================== ЗАКАЗЫ ====================

class OrderService:
    """Сервис для работы с заказами"""
    
    @staticmethod
    def get_my_orders_context(request):
        """Получить контекст моих заказов"""
        orders = Order.objects.filter(user=request.user).select_related('car').order_by('-created_at')
        return {'orders': orders}
    
    @staticmethod
    def get_order_success_context(request, order_id):
        """Получить контекст успешного заказа"""
        order = Order.objects.get(id=order_id, user=request.user)
        return {'order': order}
    
    @staticmethod
    def create_orders_from_cart(user):
        """Создать заказы из корзины"""
        cart_items = Cart.objects.filter(user=user).select_related('car')
        
        if not cart_items.exists():
            return None, 'Ваша корзина пуста'
        
        orders = []
        cars_info = []
        
        for cart_item in cart_items:
            car = cart_item.car
            
            if not car.available:
                continue
            
            # Создаём заказ
            order = Order.objects.create(
                user=user,
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
            return None, 'Не удалось оформить заказ'
        
        return orders, cars_info
    
    @staticmethod
    def send_order_confirmation_email(user, orders, cars_info):
        """Отправить email с подтверждением заказа"""
        try:
            subject = f'Подтверждение заказа #{orders[0].id} - CarShop'
            
            # HTML версия письма
            html_message = render_to_string('core/email/order_confirmation.html', {
                'user': user,
                'cars': cars_info,
                'total_price': sum(car['price'] for car in cars_info),
                'order_id': orders[0].id,
            })
            
            # Текстовая версия письма
            plain_message = f"""
Здравствуйте, {user.username}!

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
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True, f'Заказ успешно оформлен! Письмо с подтверждением отправлено на {user.email}'
        except Exception as e:
            return False, f'Заказ оформлен, но не удалось отправить email: {str(e)}'


# ==================== ОТЗЫВЫ ====================

class ReviewService:
    """Сервис для работы с отзывами"""
    
    @staticmethod
    def get_orders_without_review(user, seller):
        """Получить заказы без отзывов"""
        completed_orders = Order.objects.filter(
            user=user,
            car__seller=seller,
            status='completed'
        ).select_related('car')
        
        orders_without_review = []
        for order in completed_orders:
            if not Review.objects.filter(order=order).exists():
                orders_without_review.append(order)
        
        return orders_without_review
    
    @staticmethod
    def can_add_review(user, seller, order):
        """Проверить, может ли пользователь оставить отзыв"""
        if user == seller:
            return False, 'Вы не можете оставить отзыв самому себе'
        
        if Review.objects.filter(order=order).exists():
            return False, 'Вы уже оставили отзыв к этому заказу'
        
        return True, None
    
    @staticmethod
    def create_review(seller, buyer, order, rating, comment):
        """Создать отзыв"""
        return Review.objects.create(
            seller=seller,
            buyer=buyer,
            order=order,
            rating=rating,
            comment=comment
        )
    
    @staticmethod
    def get_add_review_context(request, seller_id, order_id):
        """Получить контекст для добавления отзыва"""
        from django.contrib.auth.models import User
        seller = User.objects.get(id=seller_id)
        order = Order.objects.get(id=order_id, user=request.user, car__seller=seller, status='completed')
        
        return {
            'seller': seller,
            'order': order,
        }
    
    @staticmethod
    def process_add_review(request, seller, order, form):
        """Обработать добавление отзыва"""
        if form.is_valid():
            ReviewService.create_review(
                seller=seller,
                buyer=request.user,
                order=order,
                rating=form.cleaned_data['rating'],
                comment=form.cleaned_data['comment']
            )
            return True, 'Спасибо за ваш отзыв!'
        return False, None
    
    @staticmethod
    def process_edit_review(review, form):
        """Обработать редактирование отзыва"""
        if form.is_valid():
            form.save()
            return True, 'Отзыв успешно обновлен!'
        return False, None
    
    @staticmethod
    def process_delete_review(review):
        """Обработать удаление отзыва"""
        seller_id = review.seller.id
        review.delete()
        return seller_id, 'Отзыв успешно удален!'


# ==================== ЧАТЫ ====================

class ChatService:
    """Сервис для работы с чатами"""
    
    @staticmethod
    def get_chats_list_context(request):
        """Получить контекст для списка чатов"""
        chats = Chat.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        ).select_related('user1', 'user2', 'car').prefetch_related('messages')
        
        chats_data = []
        total_unread = 0
        
        for chat in chats:
            other_user = chat.get_other_user(request.user)
            last_message = chat.get_last_message()
            unread_count = chat.get_unread_count(request.user)
            total_unread += unread_count
            
            chats_data.append({
                'chat': chat,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': unread_count,
            })
        
        return {
            'chats_data': chats_data,
            'total_unread': total_unread,
        }
    
    @staticmethod
    def get_chat_detail_context(request, chat_id):
        """Получить контекст для детального просмотра чата"""
        chat = Chat.objects.get(id=chat_id)
        
        # Отмечаем сообщения как прочитанные
        Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        messages_list = chat.messages.select_related('sender').order_by('created_at')
        other_user = chat.get_other_user(request.user)
        
        return {
            'chat': chat,
            'messages_list': messages_list,
            'other_user': other_user,
        }
    
    @staticmethod
    def create_message(chat, sender, text):
        """Создать сообщение"""
        message = Message.objects.create(
            chat=chat,
            sender=sender,
            text=text
        )
        chat.save()
        return message
    
    @staticmethod
    def get_or_create_chat(user1, user2, car):
        """Получить или создать чат"""
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        chat, created = Chat.objects.get_or_create(
            user1=user1,
            user2=user2,
            car=car
        )
        
        return chat, created
    
    @staticmethod
    def process_start_chat(request, seller_id, car_id):
        """Обработать начало чата"""
        from django.contrib.auth.models import User
        seller = User.objects.get(id=seller_id)
        car = Car.objects.get(id=car_id)
        
        if request.user == seller:
            return None, False, 'Вы не можете начать чат с самим собой', car_id
        
        chat, created = ChatService.get_or_create_chat(request.user, seller, car)
        
        message = f'Чат с {seller.username} создан' if created else None
        return chat, created, message, None


# ==================== ПРОФИЛЬ ====================

class ProfileService:
    """Сервис для работы с профилем"""
    
    @staticmethod
    def get_seller_profile_context(request, user_id):
        """Получить контекст профиля продавца"""
        from django.contrib.auth.models import User
        seller = User.objects.get(id=user_id)
        profile, _ = UserProfile.objects.get_or_create(user=seller)
        
        cars_for_sale = Car.objects.filter(seller=seller, available=True)
        reviews = Review.objects.filter(seller=seller).select_related('buyer', 'order__car')
        
        orders_without_review = []
        if request.user.is_authenticated and request.user != seller:
            orders_without_review = ReviewService.get_orders_without_review(request.user, seller)
        
        return {
            'seller': seller,
            'profile': profile,
            'cars_for_sale': cars_for_sale,
            'reviews': reviews,
            'orders_without_review': orders_without_review,
            'average_rating': profile.get_average_rating(),
            'reviews_count': profile.get_reviews_count(),
            'sales_count': profile.get_sales_count(),
        }
    
    @staticmethod
    def get_my_profile_context(request):
        """Получить контекст личного профиля"""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        reviews = Review.objects.filter(seller=request.user).select_related('buyer')
        
        return {
            'profile': profile,
            'reviews': reviews,
            'average_rating': profile.get_average_rating(),
            'reviews_count': profile.get_reviews_count(),
            'sales_count': profile.get_sales_count(),
        }
    
    @staticmethod
    def process_edit_profile(request, form):
        """Обработать редактирование профиля"""
        if form.is_valid():
            form.save()
            return True, 'Профиль успешно обновлен!'
        return False, None
    
    @staticmethod
    def process_change_password(request, form):
        """Обработать смену пароля"""
        if not form.is_valid():
            return False, None
        
        old_password = form.cleaned_data['old_password']
        new_password1 = form.cleaned_data['new_password1']
        new_password2 = form.cleaned_data['new_password2']
        
        if not request.user.check_password(old_password):
            return False, 'Неверный текущий пароль'
        
        if new_password1 != new_password2:
            return False, 'Новые пароли не совпадают'
        
        if len(new_password1) < 8:
            return False, 'Пароль должен содержать минимум 8 символов'
        
        request.user.set_password(new_password1)
        request.user.save()
        
        return True, 'Пароль успешно изменен!'


# ==================== АУТЕНТИФИКАЦИЯ ====================

class AuthService:
    """Сервис для аутентификации"""
    
    @staticmethod
    def process_registration(request, form):
        """Обработать регистрацию"""
        if form.is_valid():
            user = form.save()
            return True, user, 'Регистрация прошла успешно! Добро пожаловать!'
        return False, None, None
    
    @staticmethod
    def process_login(request, form):
        """Обработать вход"""
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = None
            
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            
            if user is not None:
                return True, user, f'Добро пожаловать, {username}!'
        
        return False, None, None
