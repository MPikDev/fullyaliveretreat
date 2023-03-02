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
            
            The pictures have been upload and you can find them on the website: <a href="FullyAliveRetreat.com">Fully Alive Retreat</a> or this link: <a href="https://www.dropbox.com/sh/3dbc5a0hxp62qx4/AABqhG6u_8DGkHNxYFn06HT5a?dl=0" target="_blank">Pictures</a>.               
            
             """ % camper.first_name
        yag.send(
            to=receiver_email,
            subject="Pictures - Fully Alive Retreat",
            contents=body,
        )
        print( camper.first_name, camper.pk)


def email_survey():
    # final_paid_campers_info = Camper.objects.filter(paid=True).order_by('pk')
    final_paid_campers_info = Camper.objects.filter(paid=True, pk__gt=193).order_by('pk')
    # final_paid_campers_info = Camper.objects.filter(pk=4)

    print ('emails going to send out:', len(final_paid_campers_info))
    # for c in final_paid_campers_info:
    #     print c.first_name , c.pk
    send_email(final_paid_campers_info)


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print ('starting')
        email_survey()
        print ('finished ', time.time() - start)
