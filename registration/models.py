# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Camper(models.Model):
    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    date_of_birth = models.DateTimeField()
    gender = models.CharField(
        max_length=1
        , choices=(
            ('m', 'male'),
            ('f', 'female'),
        ),
        null=True,
        default=None,
        verbose_name="Gender",
        help_text="Select the gender. 'None' means legacy campers."
    )
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
    mug = models.BooleanField(default=False)
    region = models.CharField(
        max_length=8
        , choices=(
            ('oregon', 'Oregon Region'),
            ('seattle', 'Seattle Region'),
            ('spokane', 'Spokane Region'),
        ),
        null=True,
        default='None',
        verbose_name="Activity",
        help_text="Select the t-shirt size for the camper. 'None' means no t-shirt is needed."
    )
    activity = models.CharField(
        max_length=4
        , choices=(
            ('ski', 'Ski/Snowboard'),
            ('tub', 'Tubing'),
            ('stay', 'Stay at the Cabin'),
        ),
        null=True,
        default='None',
        verbose_name="Activity",
        help_text="Select the t-shirt size for the camper. 'None' means no t-shirt is needed."
    )
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
            ('3XL', '3 Extra Large'),
            ('4XL', '4 Extra Large'),
            ('5XL', '5 Extra Large'),
        ),
        null=True,
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
            ('3XL', '3 Extra Large'),
            ('4XL', '4 Extra Large'),
            ('5XL', '5 Extra Large'),
        ),
        null=True,
        default='None',
        verbose_name="Sweat Shirt Size",
        help_text="Select the sweat shirt size for the camper. 'None' means no sweat shirt is needed."
    )
    paypal = models.CharField(max_length=48, default='untouched')
    paid = models.BooleanField()
    email_sent = models.BooleanField(default=False)
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
