# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Camper(models.Model):
    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    date_of_birth = models.DateTimeField()
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=48)
    state = models.CharField(max_length=48)
    med_notes = models.CharField(max_length=400)
    church = models.CharField(max_length=100)
    pastor = models.CharField(max_length=100)
    pastor_number = models.CharField(max_length=15, null=True, default=None)
    church_member = models.BooleanField()
    not_married = models.BooleanField(default=False)
    tshirt_size = models.CharField(
        max_length=4
        , choices=(
            ('None', 'None'),
            ('XS', 'Extra Small'),
            ('S', 'Small'),
            ('M', 'Medium'),
            ('L', 'Large'),
            ('XL', 'Extra Large'),
            ('XXL', 'Extra Extra Large'),
        ),
        default='None',
        verbose_name="T-shirt Size",
        help_text="Select the t-shirt size for the camper. 'None' means no t-shirt is needed."
    )
    swshirt_size = models.CharField(
        max_length=4,
        choices=(
            ('None', 'None'),
            ('XS', 'Extra Small'),
            ('S', 'Small'),
            ('M', 'Medium'),
            ('L', 'Large'),
            ('XL', 'Extra Large'),
            ('XXL', 'Extra Extra Large'),
        ),
        default='None',
        verbose_name="Swim Shirt Size",
        help_text="Select the swim shirt size for the camper. 'None' means no swim shirt is needed."
    )
    paypal = models.CharField(max_length=48, default='untouched')
    paid = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    camp_filter = models.CharField(max_length=48, default='not caught')

    def __unicode__(self):
        return u"{0} {1}, church member: {2}, paided: {3}".format(self.first_name, self.last_name, self.church_member, self.paid)

    def __str__(self):
        return u"{0} {1}, church member: {2}, paided: {3}".format(self.first_name, self.last_name, self.church_member, self.paid)

    # first default for paypal was
    # 1. earilier
    # 2. untouched

    # when a new reg is in it will be set to
    # reg
