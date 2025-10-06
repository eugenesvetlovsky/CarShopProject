from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Car(models.Model):

    brand = models.CharField(max_length=50, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    year = models.IntegerField(verbose_name='Год выпуска')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='cars/', blank=True, null=True, verbose_name='Изображение')
    available = models.BooleanField(default=True, verbose_name='Доступен')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars_for_sale', null=True, blank=True, verbose_name='Продавец')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

class Order(models.Model):

    STATUS_CHOICES = (
        ('pending', 'В ожидании'),
        ('approved', 'Подтверждён'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.car} by {self.user.username}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='in_carts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.car}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.car}"

class Review(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews', verbose_name='Продавец')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews', verbose_name='Покупатель')
    rating = models.IntegerField(choices=[(i, f'{i} звезд' if i > 1 else f'{i} звезда') for i in range(1, 6)], verbose_name='Рейтинг')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ('seller', 'buyer')  # Один покупатель может оставить только один отзыв продавцу

    def __str__(self):
        return f"Отзыв от {self.buyer.username} для {self.seller.username} - {self.rating} звезд"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    def get_average_rating(self):
        avg = self.user.received_reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None
    
    def get_reviews_count(self):
        return self.user.received_reviews.count()
    
    def get_sales_count(self):
        # Количество проданных автомобилей
        return Order.objects.filter(car__seller=self.user, status='completed').count()
    
    def __str__(self):
        return f"Профиль {self.user.username}"
