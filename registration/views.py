# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,render_to_response
from django.views.decorators.csrf import csrf_exempt
from registration.models import Camper
from django.core.urlresolvers import reverse
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_COMPLETED
from django.conf import settings
import datetime


def home(request):
    return render(request, 'home.html')

def full(request):
    return render(request, 'full.html')


def register(request):
    total_campers = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).count()

    if total_campers > 200:
        return render(request, 'full.html')

    camper = {'total_campers': total_campers}
    return render(request, 'register.html', camper)


def info(request):
    return render(request, 'info.html')


def reg(request):
    total_campers = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).count()

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
    paypal = 'reg',
    paid = False
    # timestamp = datetime.datetime.now()
    )

    invalid_post = False
    error_message = []

    for key, item in camper.iteritems():
        if item is u"":
            if key != "med_notes":
                error_message.append("Not all info with * is filled in")
                invalid_post = True
                break

    if camper['email'] != camper['email_v']:
        error_message.append("The emails are not the same")
        invalid_post = True

    # check if from jquery datetime
    date_of_birth_limit = datetime.datetime(1997, 6, 14, 0, 0)
    if camper['date_of_birth'].find('/') == 2:
        split_date = camper['date_of_birth'].split('/')
        year = split_date[2]
        day = split_date[1]
        month = split_date[0]
        if year != "" and day != "" and month != "":
            dob = datetime.datetime.strptime(camper['date_of_birth'], '%m/%d/%Y')
            if dob > date_of_birth_limit:
                error_message.append("Not old enough to go to camp")
                invalid_post = True
                camper['date_of_birth'] = datetime.datetime.strptime(camper['date_of_birth'], '%m/%d/%Y')
    elif camper['date_of_birth'].find('-') == 4:
        split_date = camper['date_of_birth'].split('-')
        year = split_date[0]
        day = split_date[2]
        month = split_date[1]
        if year != "" and day != "" and month != "":
            dob = datetime.datetime.strptime(camper['date_of_birth'], '%Y-%m-%d')
            if dob > date_of_birth_limit:
                error_message.append("Not old enough to go to camp")
                invalid_post = True
    else:
        error_message.append("Format of date is wrong")
        invalid_post = True

    # removed email check because will check just check who paid instead
    # camper_check = Camper.objects.filter(email=camper['email'])
    # if camper_check:
    #     error_message.append("This email is already in use")
    #     invalid_post = True

    if invalid_post:
        camper["error_message"] = error_message
        camper["total_campers"] = total_campers
        return render(request, 'register.html', camper)

    del camper['email_v']
    camper = Camper.objects.create(**camper)
    data = dict(camper_id=camper.id)
    return pay_now(request, 'pay_now.html', data)


def pay_now(request, *args, **kwargs):
    data = args
    camper_id = data[1]['camper_id']

    # What you want the button to do.
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": "170.00",
        "item_name": "registration for camp",
        'currency_code': 'USD',
        "invoice": camper_id,
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri(reverse('your-return-view')),
        "cancel_return": request.build_absolute_uri(reverse('your-cancel-view')),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render(request, "pay_now.html", context)

@csrf_exempt
def return_url(request):
    return render_to_response('success.html')

@csrf_exempt
def canceled_url(request):
    return render_to_response('cancel.html')

def error(request):
    return render_to_response('error.html')

def not_found(request):
    return render_to_response('not_found.html')
