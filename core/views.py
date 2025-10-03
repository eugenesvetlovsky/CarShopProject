from django.shortcuts import render, get_object_or_404
from .models import Car

def car_list(request):
    cars = Car.objects.filter(available=True)
    return render(request, 'core/car_list.html', {'cars': cars})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id, available=True)
    return render(request, 'core/car_detail.html', {'car': car})
