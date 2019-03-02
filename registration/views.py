# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
import datetime
from registration.models import Camper

# Create your views here.


# from django.core.urlresolvers import reverse
# from django.shortcuts import render
# from paypal.standard.forms import PayPalPaymentsForm
#
# def view_that_asks_for_money(request):
#
#     # What you want the button to do.
#     paypal_dict = {
#         "business": "receiver_email@example.com",
#         "amount": "10000000.00",
#         "item_name": "name of the item",
#         "invoice": "unique-invoice-id",
#         "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
#         "return": request.build_absolute_uri(reverse('your-return-view')),
#         "cancel_return": request.build_absolute_uri(reverse('your-cancel-view')),
#         "custom": "premium_plan",  # Custom command to correlate to some function later (optional)
#     }
#
#     # Create the instance.
#     form = PayPalPaymentsForm(initial=paypal_dict)
#     context = {"form": form}
#     return render(request, "payment.html", context)

def home(request):
    return render(request, 'home.html')


def register(request):
    total_campers = Camper.objects.all().count()

    if total_campers > 200:
        return render(request, 'full.html')

    camper = {'total_campers': total_campers}
    return render(request, 'register.html', camper)


def info(request):
    return render(request, 'info.html')


def reg(request):
    total_campers = Camper.objects.all().count()

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
    error_message = []

    for key, item in camper.iteritems():
        if item is u"":
            if key != "med_notes":
                error_message.append("Fill in all the info with *")
                invalid_post = True
                break

    if camper['email'] != camper['email_v']:
        error_message.append("The emails are not the same")
        invalid_post = True

    year = camper['date_of_birth'].split('-')[0]
    if year != "":
        if int(year) > 1996:
            error_message.append("Not old enough to go to camp")
            invalid_post = True

    camper_check = Camper.objects.filter(email=camper['email'])
    if camper_check:
        error_message.append("This email is already in use")
        invalid_post = True

    if invalid_post:
        camper["error_message"] = error_message
        camper["total_campers"] = total_campers
        return render(request, 'register.html', camper)

    del camper['email_v']
    camper = Camper.objects.create(**camper)

    return render(request, 'success.html')


# def ipn(request, *args, **kwargs):
#     import pdb
#     pdb.set_trace()
#
# def paypal():
#     # !/usr/bin/python
#
#     '''This module processes PayPal Instant Payment Notification messages (IPNs).'''
#
#     import sys
#     import urllib.parse
#     import requests
#
#     VERIFY_URL_PROD = 'https://ipnpb.paypal.com/cgi-bin/webscr'
#     VERIFY_URL_TEST = 'https://ipnpb.sandbox.paypal.com/cgi-bin/webscr'
#
#     # Switch as appropriate
#     VERIFY_URL = VERIFY_URL_TEST
#
#     # CGI preamble
#     print ('content-type: text/plain')
#     print ()
#
#     # Read and parse query string
#     param_str = sys.stdin.readline().strip()
#     params = urllib.parse.parse_qsl(param_str)
#
#     # Add '_notify-validate' parameter
#     params.append(('cmd', '_notify-validate'))
#
#     # Post back to PayPal for validation
#
#     headers = {'content-type': 'application/x-www-form-urlencoded',
#                'user-agent': 'Python-IPN-Verification-Script'}
#     r = requests.post(VERIFY_URL, params=params, headers=headers, verify=True)
#     r.raise_for_status()
#
#     # Check return message and take action as needed
#     if r.text == 'VERIFIED':
#         pass
#     elif r.text == 'INVALID':
#         pass
#     else:
#         pass
