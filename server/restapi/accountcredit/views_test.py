import datetime

from restapi.views_test import RESTAPITest
from django.core.urlresolvers import reverse

import dash.models
from utils.magic_mixer import magic_mixer


class AccountCreditsTest(RESTAPITest):

    @classmethod
    def credit_repr(
        cls,
        id=123,
        createdOn=datetime.datetime.now(),
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        total='500',
        allocated='200.0',
        available='300.0',
    ):
        return cls.normalize({
            'id': id,
            'createdOn': createdOn,
            'startDate': startDate,
            'endDate': endDate,
            'total': total,
            'allocated': allocated,
            'available': available,
        })

    def validate_against_db(self, credit):
        credit_db = dash.models.CreditLineItem.objects.get(pk=credit['id'])
        expected = self.credit_repr(
            id=str(credit_db.id),
            createdOn=credit_db.created_dt.date(),
            startDate=credit_db.start_date,
            endDate=credit_db.end_date,
            total=credit_db.effective_amount(),
            allocated=credit_db.get_allocated_amount(),
            available=credit_db.effective_amount() - credit_db.get_allocated_amount(),
        )
        self.assertEqual(expected, credit)

    def test_account_credits_get(self):
        r = self.client.get(
            reverse('accounts_credits_details', kwargs={'account_id': 186, 'credit_id': 861})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])

    def test_account_credits_get_credit_doesnt_exist(self):
        r = self.client.get(
            reverse('accounts_credits_details', kwargs={'account_id': 186, 'credit_id': 1234})
        )
        self.assertResponseError(r, 'DoesNotExist')

    def test_account_credits_get_account_doesnt_exist(self):
        r = self.client.get(
            reverse('accounts_credits_details', kwargs={'account_id': 123, 'credit_id': 861})
        )
        self.assertResponseError(r, 'MissingDataError')

    def test_account_credits_list(self):
        r = self.client.get(reverse('accounts_credits_list', kwargs={'account_id': 186}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

    def test_account_credits_pagination(self):
        account = magic_mixer.blend(dash.models.Account, users=[self.user])
        magic_mixer.cycle(10).blend(dash.models.CreditLineItem, account=account, end_date=datetime.date.today())
        r = self.client.get(
            reverse('accounts_credits_list', kwargs={'account_id': account.id}),
        )
        r_paginated = self.client.get(
            reverse('accounts_credits_list', kwargs={'account_id': account.id}),
            {'limit': 2, 'offset': 5},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json['data'][5:7], resp_json_paginated['data'])
