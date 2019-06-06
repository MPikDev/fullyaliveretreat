from django.core.management.base import BaseCommand
from registration.models import Camper
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.models import PayPalIPN
from registration.views import filter_campers
import time


def paided():
    total_paid_campers_pk = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).values_list('invoice', flat=True)
    int_pks = []
    for pk in total_paid_campers_pk:
        int_pks.append(int(pk))

    Camper.objects.filter(pk__in=int_pks).update(paid=True)



class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        print 'starting'
        paided()
        print 'finished ', time.time() - start

