# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import yagmail
from registration.models import Camper
from django.core.urlresolvers import reverse
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_REFUNDED
from django.conf import settings
import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from personal_code.settings import SPRING_2020_CAMP, SPRING_2019_CAMP, FALL_2020_CAMP, FALL_2021_CAMP, \
    GLOBAL_OPEN_REG_FLAG, SUMMER_2022_CAMP, SUMMER_2023_CAMP, SUMMER_2024_CAMP, SUMMER_2025_CAMP

# FIlTER_2020 = datetime.datetime(2020, 1, 1, 1, 33, 24, 755599)
# FIlTER_FALL_2020 = datetime.datetime(2020, 7, 1, 1, 33, 24, 755599)

# FIlTER_2021 = datetime.datetime(2021, 5, 1, 1, 33, 24, 755599)
# FIlTER_FALL_2021 = datetime.datetime(2021, 9, 3, 1, 33, 24, 755599)

# FIlTER_2022 = datetime.datetime(2021, 10, 1, 1, 33, 24, 755599)
# FIlTER_FALL_2022 = datetime.datetime(2022, 8, 14, 1, 33, 24, 755599)

# FIlTER_2023 = datetime.datetime(2022, 8, 15, 1, 33, 24, 755599)
# FIlTER_FALL_2023 = datetime.datetime(2023, 8, 14, 1, 33, 24, 755599)

# FIlTER_2024 = datetime.datetime(2023, 8, 15, 1, 33, 24, 755599)
# FIlTER_FALL_2024 = datetime.datetime(2024, 8, 14, 1, 33, 24, 755599)

FIlTER_2025 = datetime.datetime(2024, 9, 15, 1, 33, 24, 755599)
FIlTER_FALL_2025 = datetime.datetime(2025, 9, 14, 1, 33, 24, 755599)


def send_registration_email(camper):
    yag = yagmail.SMTP("fullyaliveretreat@gmail.com", "weqf ucmg cksi znvy")

    # HTML version with styled links
    html_content = f"""\
    <div style="font-family: sans-serif; font-size: 14px; line-height: 1.4;">
      <div>Hello {camper.first_name},</div>

      <div>You have successfully registered for <strong>Fully Alive Retreat</strong>!</div>

      <div><strong>Camp starts:</strong> August 22, 2025 at 4:00pm <a href="http://{settings.DOMAIN}/static/fullyalive.ics" style="color: #007bff; text-decoration: none;">Add to Calendar</a>
      <strong>Camp address:</strong> 18705 N Hwy 101, Rockaway Beach, OR 97136
      Join our <a href="https://t.me/+Ky9V40c6bh0yMjMx" style="color: #007bff; text-decoration: none;">Telegram group</a> to stay updated.
      <br>
      <strong>Your Order:</strong><br>
        Sweater: {camper.swshirt_size}
        T-Shirt: {camper.tshirt_size}
        Mug: {camper.mug}
      <br>
    Follow us on  <a href="https://www.instagram.com/fullyaliveretreat?igsh=MXE1aXppNmdtZDQybQ==" style="color: #007bff; text-decoration: none;"> Instagram</a>
      </div>

      <div>
    
      </div>
    </div>
    """

    yag.send(
        to=camper.email,
        subject="You're Registered to Fully Alive Retreat 2025!",
        contents=[html_content]
    )




def check_who_paid_helper():
    refund_incoices = PayPalIPN.objects.filter(payment_status=ST_PP_REFUNDED, created_at__gte=FIlTER_2025).values_list(
        'invoice', flat=True)
    unicode_total_paid_campers_pk = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED,
                                                             created_at__gte=FIlTER_2025).exclude(
        invoice__in=refund_incoices).values_list('invoice', flat=True)

    int_total_paid_campers_pk = [int(float(pk)) for pk in unicode_total_paid_campers_pk]
    no_duplicate_int_total_paid_campers_pk = list(dict.fromkeys(int_total_paid_campers_pk))

    paid_all_campers = Camper.objects.filter(pk__in=no_duplicate_int_total_paid_campers_pk)
    # for testing
    # paid_all_campers = [Camper.objects.get(pk=88)]

    print(len(paid_all_campers))  # this is for the query to be done right now
    for camper in paid_all_campers:
        camper.paid = True
        camper.save()
        # send emails to campers that have not got an email
        if not camper.email_sent:
            try:
                send_registration_email(camper)
                camper.email_sent = True
                camper.save()
            except Exception as e:
                print("email didn't send")
                print(camper)
                print(e)

    refund_incoices = [str(pk) for pk in refund_incoices]
    refund_campers = Camper.objects.filter(pk__in=refund_incoices)
    for camper in refund_campers:
        if camper.paid:
            camper.paid = False
            camper.save()


def home(request):
    return render(request, 'home.html')


def full(request):
    return render(request, 'full.html')

# @login_required(redirect_field_name='login')
def register(request):
    # return redirect('https://www.tickettailor.com/events/nwasbcyouth/1357024')
    # return render(request, 'paypal_issues.html')

    # closed
    # return render(request, 'hasnt_opened.html')

    refund_incoices = PayPalIPN.objects.filter(payment_status=ST_PP_REFUNDED, created_at__gte=FIlTER_2025).values_list('invoice',flat=True)
    total_campers = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED, created_at__gte=FIlTER_2025).exclude(invoice__in=refund_incoices).count()

    if settings.GLOBAL_OPEN_REG_FLAG:
        if total_campers > settings.MAX_CAPACITY:
            return render(request, 'closed.html')
        if datetime.datetime.now() > FIlTER_FALL_2025:
            return render(request, 'closed.html')

    camper = {'total_campers': total_campers}
    camper["max_capacity"] = settings.MAX_CAPACITY
    return render(request, 'register.html', camper)


# def info(request):
    # return render(request, 'info.html')

def info(request):
    data = {
        "max_capacity": settings.MAX_CAPACITY,
        "camp_price": settings.CAMP_PRICE,
    }
    return render(request, 'info.html', data)


def photos(request):
    return render(request, 'photos.html')


def fellowship(request):
    return render(request, 'fellowship.html')


def schedule(request):
    return render(request, 'schedule.html')


def paypal_issues(request):
    return render(request, 'paypal_issues.html')

@login_required(redirect_field_name='login')
def open_reg(request):
    settings.GLOBAL_OPEN_REG_FLAG = True
    return camper_info(request)


@login_required(redirect_field_name='login')
def close_reg(request):
    settings.GLOBAL_OPEN_REG_FLAG = False
    return camper_info(request)


@login_required(redirect_field_name='login')
def check_who_paid(request):

    check_who_paid_helper()

    return camper_info(request)


def reg(request):
    # Regisratation hasn't not opened yet
    # return render(request, 'hasnt_opened.html')

    refund_incoices = PayPalIPN.objects.filter(payment_status=ST_PP_REFUNDED, created_at__gte=FIlTER_2025).values_list(
        'invoice', flat=True)
    total_campers = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED,
                                                             created_at__gte=FIlTER_2025).exclude(
        invoice__in=refund_incoices).count()

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
    pastor_number = request.POST['camper_pastor_phone'],
    church_member = request.POST.get('camper_church_member'),
    tshirt_size = request.POST.get('tshirt_size'),
    swshirt_size = request.POST.get('swshirt_size'),
    mug = request.POST.get('camper_mug', False),
    not_married = request.POST.get('camper_not_married'),
    paypal = 'reg',
    paid = False,

    camp_filter = SUMMER_2025_CAMP,
    )
    # print(camper['church_member'],camper['not_married'])
    #cast into booleans
    try:
        camper['church_member'] = True if camper['church_member'] in ['True','true'] or camper['church_member'] is True else False
        camper['not_married'] = True if camper['not_married'] in ['True','true'] or camper['not_married'] is True else False
        camper['mug'] = True if camper['mug'] in ['True','true'] or camper['mug'] is True else False
    except:
        camper['church_member'] = False
        camper['not_married'] = False
        camper['mug'] = False

    # print(camper['church_member'],camper['not_married'])

    invalid_post = False
    error_message = []
    for key, item in camper.items():
        if item == u"":
            if key != "med_notes":
                error_message.append("Not all info with * is filled in")
                invalid_post = True
                break

    if camper['email'] != camper['email_v']:
        error_message.append("The emails are not the same")
        invalid_post = True

    # check if from jquery datetime
    date_of_birth_limit = datetime.datetime(2001, 8, 23, 0, 0)
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

    if invalid_post:
        camper["error_message"] = error_message
        camper["total_campers"] = total_campers
        camper["max_capacity"] = settings.MAX_CAPACITY
        return render(request, 'register.html', camper, status=status.HTTP_400_BAD_REQUEST)

    del camper['email_v']
    camper_object = Camper.objects.create(**camper)
    # want to save the camper to make sure we catch that this person wrote that they were married
    if not camper['not_married'] or not camper['church_member']:
        return render_to_response('married_error.html', status=status.HTTP_400_BAD_REQUEST)

    data = dict(camper_id=camper_object.id,
                sweater=False if camper_object.swshirt_size in ['None', 'null'] else True,
                tshirt=False if camper_object.tshirt_size in ['None', 'null'] else True,
                mug=camper_object.mug,
    )

    return pay_now(request, 'pay_now.html', data)


def pay_now(request, *args, **kwargs):
    data = args
    camper_info = data[1]
    camper_id = camper_info['camper_id']

    price = settings.CAMP_PRICE
    if camper_info['tshirt']:
        price += 30
    if camper_info['sweater']:
        price += 45
    if camper_info['mug']:
        price += 10


    # What you want the button to do.
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount":  f"{price}.00",
        "item_name": "Registration for Fully Alive Retreat Summer 2025",
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
    check_who_paid_helper()
    return render_to_response('success.html')

@csrf_exempt
def canceled_url(request):
    return render_to_response('cancel.html')

def error(request):
    return render_to_response('error.html')

def not_found(request):
    return render_to_response('not_found.html')

def log_in(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect('/camper_info')
    else:
        return render(request, 'login.html')

def camper_logout(request):
    logout(request)
    return render(request, 'logout.html')

@login_required(redirect_field_name='login')

def camper_info(request,  **kwargs):
    filter_camp = SUMMER_2025_CAMP
    print( 'Giving Camp',  kwargs)
    if 'camper_2021_info_fall' in kwargs:
        filter_camp = FALL_2021_CAMP
    elif 'camper_2020_info_fall' in kwargs:
        filter_camp = FALL_2020_CAMP
    elif 'camper_info_2020_spring' in kwargs:
        filter_camp = SPRING_2020_CAMP
    elif 'camper_2019_info_spring' in kwargs:
        filter_camp = SPRING_2019_CAMP
    elif 'camper_2022_info_summer' in kwargs:
        filter_camp = SUMMER_2022_CAMP
    elif 'camper_2023_info_summer' in kwargs:
        filter_camp = SUMMER_2023_CAMP
    elif 'camper_2024_info_summer' in kwargs:
        filter_camp = SUMMER_2024_CAMP

    print ('Selected Camp', filter_camp)

    paid_campers = Camper.objects.filter(camp_filter=filter_camp, paid=True).order_by('pk')
    not_paid_campers =  Camper.objects.filter(camp_filter=filter_camp, paid=False).order_by('pk')
    try:
        not_paid_and_no_duplicates_campers  = Camper.objects.filter(camp_filter=filter_camp, paid=False).distinct('email')
        len(not_paid_and_no_duplicates_campers)
    except:
        not_paid_and_no_duplicates_campers = Camper.objects.filter(camp_filter=filter_camp,paid=False)
        non_dulicate = {}
        for camper in not_paid_and_no_duplicates_campers:
            if camper.email not in non_dulicate:
                non_dulicate[camper.email] = camper

        not_paid_and_no_duplicates_campers = non_dulicate.values()
    #created keys to create tables
    base_camper = Camper().__dict__
    for item in ['_state','paypal','camp_filter']:
        del base_camper[item]
    base_camper_keys = [key for key in base_camper]

    data = {'paid_campers_info': paid_campers,
            'not_campers_info': not_paid_campers,
            'not_paid_email_info': not_paid_and_no_duplicates_campers,
            'paid_count': len(paid_campers),
            'not_count': len(not_paid_campers),
            'not_email_count': len(not_paid_and_no_duplicates_campers),
            'final_paid_campers_info':paid_campers,
            'final_paid_count': len(paid_campers),
            'camp_filter':filter_camp,
            'reg_flag': settings.GLOBAL_OPEN_REG_FLAG,
            'base_camper_keys':base_camper_keys
            }
    return render(request, 'camper_info.html', data)


def filter_campers(all_campers, int_pks):
    paid_campers_info_2020 = []
    not_campers_info_2020 = []
    not_paid_email_info_2020 = []
    paid_campers_info = []
    not_campers_info = []
    not_paid_email_info = []
    emails_2020 = []
    emails = []
    for camper in all_campers:
        if camper.id in int_pks:
            if camper.timestamp.year == 2020:
                paid_campers_info_2020.append(camper)
                emails_2020.append(camper.email)
            else:
                paid_campers_info.append(camper)
                emails.append(camper.email)

    for camper in all_campers:
        if camper.id not in int_pks:
            if camper.timestamp.year == 2020:
                not_campers_info_2020.append(camper)
                if camper.email not in emails:
                    emails_2020.append(camper.email)
                    not_paid_email_info_2020.append(camper)
            else:
                not_campers_info.append(camper)
                if camper.email not in emails:
                    emails.append(camper.email)
                    not_paid_email_info.append(camper)

    return paid_campers_info_2020, not_campers_info_2020, not_paid_email_info_2020, paid_campers_info, not_campers_info, not_paid_email_info
