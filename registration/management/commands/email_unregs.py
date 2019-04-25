from django.core.management.base import BaseCommand
from registration.models import Camper
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.models import PayPalIPN
import yagmail
import time

def send_email(list_campers):
    yag = yagmail.SMTP("fullyaliveretreat@gmail.com", "Fulllluf")

    for camper in list_campers:
        receiver_email = camper.email

        body = """\
            Hello %s,

            You are receiving this email because you have not yet paid for the Fully Alive Retreat after having registered. Also, this is a reminder that starting May 1st, the price of registration increases. 

            If you have paid and have received a PayPal confirmation, please disregard this email. However, if you have paid and have not gotten a confirmation from PayPal, please notify us by email.

            We ask that you spread the news about the Fully Alive Retreat by sharing the website www.fullyaliveretreat.com, dates and deadlines with friends and family. Thank you and God bless! We look forward to seeing June 14th.

        """ % camper.first_name
        yag.send(
            to=receiver_email,
            subject="Payment Reminder - Fully Alive Retreat",
            contents=body,
        )


def reg_not_paid():
    total_paid_campers_pk = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).values_list('invoice', flat=True)
    int_pks = []
    for pk in total_paid_campers_pk:
        int_pks.append(int(pk))

    all_campers = Camper.objects.all()
    print len(all_campers)

    paid_campers_info = []
    not_campers_info = []
    not_paid_email_info = []
    emails = []
    for camper in all_campers:
        if camper.id in int_pks:
            paid_campers_info.append(camper)
            emails.append(camper.email)

    for camper in all_campers:
        if camper.id not in int_pks:
            not_campers_info.append(camper)
            if camper.email not in emails:
                not_paid_email_info.append(camper)

    send_email(not_paid_email_info)


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print 'starting'
        reg_not_paid()
        print 'finished ', time.time() - start
