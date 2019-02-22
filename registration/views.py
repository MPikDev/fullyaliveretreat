# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'home.html')

def home2(request):
    return render(request, 'home2.html')

def register(request):
    return render(request, 'register.html')

def info(request):
    return render(request, 'info.html')