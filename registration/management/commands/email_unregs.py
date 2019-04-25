from registration.models import Camper
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.models import PayPalIPN


total_paid_campers_pk = PayPalIPN.objects.filter(payment_status=ST_PP_COMPLETED).values_list('invoice', flat=True)
int_pks = []
for pk in total_paid_campers_pk:
    int_pks.append(int(pk))

all_campers = Camper.objects.all()
print all_campers.len()

paid_campers_info = []
not_campers_info = []
not_paid_email_info = []
emails = []
for camper in all_campers:
    if camper.id in int_pks:
        paid_campers_info.append(camper)
    else:
        not_campers_info.append(camper)
        if camper.email not in emails:
            emails.append(camper.email)
            not_paid_email_info.append(camper)
