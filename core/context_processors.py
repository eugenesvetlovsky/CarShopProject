from django.db.models import Q, Count
from .models import Chat, Message


def unread_messages_count(request):
    """Контекстный процессор для отображения количества непрочитанных сообщений"""
    if request.user.is_authenticated:
        # Получаем все чаты пользователя
        user_chats = Chat.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        )
        
        # Считаем непрочитанные сообщения (не от текущего пользователя)
        total_unread = Message.objects.filter(
            chat__in=user_chats,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return {
            'total_unread_messages': total_unread
        }
    
    return {
        'total_unread_messages': 0
    }
