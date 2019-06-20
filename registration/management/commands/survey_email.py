from django.core.management.base import BaseCommand
from registration.models import Camper
from personal_code.settings import STATIC_ROOT
import yagmail
import time

def send_email(list_campers):
    yag = yagmail.SMTP("fullyaliveretreat@gmail.com", "lluFfull")
    for camper in list_campers:
        receiver_email = camper.email

        body = """\
            Hello %s,

           Thank you for coming out and joining us at the Fully Alive Retreat. We hope you had a good and blessed time. You already might have filled out the survey, but if not, this is a reminder. We would appreciate any feedback, thoughts and suggestions. Here is the link <a href="https://docs.google.com/forms/d/e/1FAIpQLSeeBRWi8hnqLVPvrwJChocqKDxWa00pDlfzCKEWZlF-Hr2HJw/viewform?usp=pp_url" target="_blank">Survey</a>.     
              
              """ % camper.first_name
        yag.send(
            to=receiver_email,
            subject="Survey - Fully Alive Retreat",
            contents=body,
        )
        print camper.first_name, camper.pk


def email_survey():
    # final_paid_campers_info = Camper.objects.filter(paid=True).order_by('pk')
    final_paid_campers_info = Camper.objects.filter(paid=True, pk__gt=176).order_by('pk')
    # final_paid_campers_info = Camper.objects.filter(pk=4)

    print 'emails going to send out:', len(final_paid_campers_info)
    # for c in final_paid_campers_info:
    #     print c.first_name , c.pk
    send_email(final_paid_campers_info)


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print 'starting'
        email_survey()
        print 'finished ', time.time() - start
