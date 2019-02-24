# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
import datetime
from registration.models import Camper

# Create your views here.

def home(request):
    return render(request, 'home.html')


def register(request):
    return render(request, 'register.html')


def info(request):
    return render(request, 'info.html')


def reg(request):
    camper = dict(
    first_name = request.POST['camper_first_name'],
    last_name = request.POST['camper_last_name'],
    date_of_birth = request.POST['camper_date_of_birth'],
    email = request.POST['camper_email'],
    email_v = request.POST['camper_email_again'],
    phone = request.POST['camper_phone'],
    city = request.POST['camper_city'],
    state = request.POST['camper_state'],
    med_notes = request.POST['camper_med_notes'],
    church = request.POST['camper_church'],
    pastor = request.POST['camper_pastor'],
    church_member = request.POST.get('camper_church_member', False),
    # paid = request.POST['camper_paid']
    paid = False
    # timestamp = datetime.datetime.now()
    )

    invalid_post = False
    error_message = ''

    for key, item in camper.iteritems():
        if item is u"":
            if key != "med_notes":
                error_message += "Fill in all the info with * \n"
                invalid_post = True
                break

    if camper['email'] != camper['email_v']:
        error_message += "The emails are not the same\n"
        invalid_post = True

    camper_check = Camper.objects.filter(email=camper['email'])
    if camper_check:
        error_message += "This email is already in use\n"
        invalid_post = True

    if invalid_post:
        camper["error_message"] = error_message
        return render(request, 'register.html', camper)

    del camper['email_v']
    camper = Camper.objects.create(**camper)

    return render(request, 'success.html')

