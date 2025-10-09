from django.db.models import Q, Count
from .models import Chat, Message, Cart, Favorite


def common_context(request):
    """Общий контекстный процессор для всех страниц"""
    context = {
        'total_unread_messages': 0,
        'cart_count': 0,
        'favorites_count': 0
    }
    
    if request.user.is_authenticated:
        # Считаем непрочитанные сообщения
        user_chats = Chat.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        )
        total_unread = Message.objects.filter(
            chat__in=user_chats,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Считаем товары в корзине
        cart_count = Cart.objects.filter(user=request.user).count()
        
        # Считаем избранные товары
        favorites_count = Favorite.objects.filter(user=request.user).count()
        
        context.update({
            'total_unread_messages': total_unread,
            'cart_count': cart_count,
            'favorites_count': favorites_count
        })
    
    return context
