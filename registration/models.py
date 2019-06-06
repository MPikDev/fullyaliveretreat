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
    church_member = models.BooleanField()
    paypal = models.CharField(max_length=48, default='untouched')
    paid = models.BooleanField()
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"{0} {1}, church member: {2}, paided: {3}".format(self.first_name, self.last_name, self.church_member, self.paid)


    # first default for paypal was
    # 1. earilier
    # 2. untouched

    # when a new reg is in it will be set to
    # reg