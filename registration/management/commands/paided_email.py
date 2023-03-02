from django.core.management.base import BaseCommand
from registration.models import Camper
from personal_code.settings import STATIC_ROOT
import yagmail
import time

def send_email(list_campers):
    yag = yagmail.SMTP("fullyaliveretreat@gmail.com", "REMOVED")
    for camper in list_campers:
        receiver_email = camper.email

        body = """\
            Hello %s,

            Fully Alive Retreat is around the corner and we wanted to remind you that registration is Friday June 14th from 4 - 6 PM. The building in which registration will be held is the Welcome Center. The location is indicated on the map attached to this email. During registration you will get a map of the camp, told where your cabin will be, and you will have to sign a camp waiver form. If you are not able to register 4-6 PM, please reply to this email or contact Mark (509-979-5419) and mention when you will be arriving. Thank you.

        """ % camper.first_name
        yag.send(
            to=receiver_email,
            subject="Check-in Details - Fully Alive Retreat",
            contents=body,
            attachments= STATIC_ROOT +'/registration/camp_map_reg.pdf'
        )
        print (camper.first_name, camper.pk)


def email_paided():
    final_paid_campers_info = Camper.objects.filter(paid=True, pk__gt=155).order_by('pk')
    # final_paid_campers_info = Camper.objects.filter(paid=True, pk__gt=23).order_by('pk')
    # final_paid_campers_info = Camper.objects.filter(pk=122)

    print( 'emails going to send out:', len(final_paid_campers_info))
    # for c in final_paid_campers_info:
    #     print c.first_name , c.pk
    send_email(final_paid_campers_info)


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print( 'starting')
        email_paided()
        print ('finished ', time.time() - start)
