from django.core.management.base import BaseCommand
from registration.models import Camper
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.models import PayPalIPN
from registration.views import filter_campers
import yagmail
import time

def send_email(list_campers):
    yag = yagmail.SMTP("fullyaliveretreat@gmail.com", "lluFfull")
    dont_send_list = [171, 98, 106]
    for camper in list_campers:
        if camper.id not in dont_send_list:
            receiver_email = camper.email

            body = """\
                Hello %s,

                You are receiving this email because you have not yet paid for the Fully Alive Retreat after having registered. The registration closes today at midnight.

                If you have paid and have received a PayPal confirmation, please disregard this email. However, if you have paid and have not gotten a confirmation from PayPal, please notify us by email.

                Thank you and God bless! We look forward to seeing June 14th.

            """ % camper.first_name
            yag.send(
                to=receiver_email,
                subject="Deadline Reminder - Fully Alive Retreat",
                contents=body,
            )


def reg_not_paid():
    total_paid_campers_pk = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).values_list('invoice', flat=True)
    int_pks = []
    for pk in total_paid_campers_pk:
        int_pks.append(int(pk))

    all_campers = Camper.objects.all()
    print (len(all_campers))

    paid_campers_info, not_campers_info, not_paid_email_info = filter_campers(all_campers, int_pks)

    print ('emails going to send out:', len(not_paid_email_info))
    send_email(not_paid_email_info)


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print ('starting')
        reg_not_paid()
        print ('finished ', time.time() - start)
