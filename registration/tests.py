# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import json

from django.test import TestCase

# Create your tests here.
from rest_framework import status

from registration.models import Camper


class CamperRegistartionTests(TestCase):
    data = {
        "camper_first_name": "Mark",
        "camper_last_name": "Pikulik",
        "camper_gender": "m",
        'camper_date_of_birth': '2000-08-25',
        'camper_email': 'het7ga@gmail.com',
        'camper_email_again': 'het7ga@gmail.com',
        'camper_phone': '5099795419',
        'camper_city': 'pullman',
        'camper_state': 'WA',
        'camper_med_notes': '',
        'camper_church': 'asdf',
        'camper_pastor': 'asdf',
        'camper_pastor_phone': 'a345345',
        'camper_church_member': True,
        'camper_not_married': True,
    }

    def test_sucessful_camper_with_all_info(self):
        data = copy.deepcopy(self.data)
        response = self.client.post('/register',data=data)
        assert response.status_code == status.HTTP_200_OK

        camper = Camper.objects.first()
        print(f'{camper=}')
        assert camper.first_name == data['camper_first_name']
        assert camper.last_name == data['camper_last_name']
        assert camper.email == data['camper_email']
        assert camper.phone == data['camper_phone']
        assert camper.city == data['camper_city']
        assert camper.state == data['camper_state']
        assert camper.med_notes == data['camper_med_notes']
        assert camper.church == data['camper_church']
        assert camper.pastor == data['camper_pastor']
        assert camper.pastor_number == data['camper_pastor_phone']
        assert camper.church_member == data['camper_church_member']
        assert camper.not_married == data['camper_not_married']


    def test_redirect_camper_married(self):
        data = copy.deepcopy(self.data)
        data['camper_not_married'] = False

        response = self.client.post('/register',data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.assertTemplateUsed(response, 'married_error.html')
        camper = Camper.objects.first()
        assert camper.first_name == data['camper_first_name']
        assert camper.last_name == data['camper_last_name']
        assert camper.email == data['camper_email']
        assert camper.phone == data['camper_phone']
        assert camper.city == data['camper_city']
        assert camper.state == data['camper_state']
        assert camper.med_notes == data['camper_med_notes']
        assert camper.church == data['camper_church']
        assert camper.pastor == data['camper_pastor']
        assert camper.pastor_number == data['camper_pastor_phone']
        assert camper.church_member == data['camper_church_member']
        assert camper.not_married == data['camper_not_married']

    def test_redirect_camper_not_all_info_is_filled_in(self):
        empty_list = ["camper_first_name", "camper_last_name", 'camper_phone', 'camper_city', 'camper_state', 'camper_church',
                      'camper_pastor', 'camper_pastor_phone']
        check_empty_list = ["first_name", "last_name", 'phone', 'city', 'state', 'church', 'pastor', 'pastor_number']
        for i, key in enumerate(empty_list):
            data = copy.deepcopy(self.data)
            data[key] = ''
            response = self.client.post('/register', data=data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            camper = Camper.objects.first()
            assert camper is None
            # print(key)
            print(response.context.get('error_message'))
            assert response.context.get('error_message') == [f"Not all info with * is filled in, missing: ['{check_empty_list[i]}']"]

    def test_redirect_camper_not_all_info_is_filled_in_date(self):
        data = copy.deepcopy(self.data)
        data['camper_date_of_birth'] = ''
        response = self.client.post('/register', data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        camper = Camper.objects.first()
        assert camper is None
        print(response.context.get('error_message'))
        assert response.context.get('error_message') == ["Not all info with * is filled in, missing: ['date_of_birth']", 'Format of date is wrong']

    def test_redirect_camper_not_all_info_is_filled_in_email(self):
        data = copy.deepcopy(self.data)
        data['camper_email'] = ''
        response = self.client.post('/register', data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        camper = Camper.objects.first()
        assert camper is None
        print(response.context.get('error_message'))
        assert response.context.get('error_message') == ["Not all info with * is filled in, missing: ['email']", 'The emails are not the same']

    def test_redirect_camper_not_all_info_is_filled_in_v_email(self):
        data = copy.deepcopy(self.data)
        data['camper_email_again'] = ''
        response = self.client.post('/register', data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        camper = Camper.objects.first()
        assert camper is None
        print(response.context.get('error_message'))
        assert response.context.get('error_message') == ["Not all info with * is filled in, missing: ['email_v']", 'The emails are not the same']


    def test_birthday_check(self):
        # todo add mock for date.today and retry different times
        data = copy.deepcopy(self.data)
        checks = [{'dob': '06/16/2010',
                  'error':["Not old enough to go to camp"],
                   'status': status.HTTP_400_BAD_REQUEST,},
                  {'dob': '06/16/1981',
                   'error': ["Too old to go to camp"],
                   'status': status.HTTP_400_BAD_REQUEST, },
                  {'dob': '06/16/1982',
                   'error': None,
                   'status': status.HTTP_200_OK, },
                  ]
        for check in checks:
            print(check)
            data['camper_date_of_birth'] = check['dob']
            response = self.client.post('/register', data=data)
            self.assertEqual(response.status_code, check['status'])
            self.assertEqual(response.context.get('error_message'), check['error'])

