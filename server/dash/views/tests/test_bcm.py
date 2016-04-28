#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.test import TestCase

from zemauth.models import User
from dash import models, constants
from reports.models import BudgetDailyStatement


class BCMViewTestCase(TestCase):
    fixtures = ['test_bcm.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        self.client.login(username=self.user.email, password='secret')

    def add_permission(self, name):
        permission = Permission.objects.get(codename=name)
        self.user.user_permissions.add(permission)


class AccountCreditViewTest(BCMViewTestCase):

    def test_permissions(self):
        url = reverse('accounts_credit', kwargs={'account_id': 1})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url, json.dumps({'cancel': 1}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        url = reverse('accounts_credit', kwargs={'account_id': 1})

        self.add_permission('account_credit_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['data'], {
            "active": [
                {
                    "available": "0.0000",
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "comment": "Test case",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "past": [],
            "totals": {
                "available": "0.0000",
                "allocated": "100000.0000",
                "total": "100000.0000",
                "past": "0",
            }
        })

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2016, 11, 11)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content)['data'], {
            "active": [],
            "past": [
                {
                    "available": "0.0000",
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "comment": "Test case",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "totals": {
                "available": "0.0000",
                "allocated": "0",
                "past": "100000.0000",
                "total": "100000.0000"
            }
        })

    def test_post(self):
        url = reverse('accounts_credit', kwargs={'account_id': 1})

        credit = models.CreditLineItem.objects.create(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal('0.2'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(models.CreditLineItem.objects.filter(
            status=constants.CreditLineItemStatus.CANCELED
        ).count(), 0)
        request_data = {'cancel': [credit.pk]}

        self.add_permission('account_credit_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, json.dumps(request_data),
                                        content_type='application/json')
        response_data = json.loads(response.content)
        self.assertTrue(credit.pk in response_data['data']['canceled'])
        self.assertEqual(models.CreditLineItem.objects.filter(
            status=constants.CreditLineItemStatus.CANCELED
        ).count(), 1)

    def test_put(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment='TESTCASE_PUT')))

        url = reverse('accounts_credit', kwargs={'account_id': 1})

        request_data = {}

        self.add_permission('account_credit_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data))

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertTrue('amount' in response_data['data']['errors'])
        self.assertTrue('start_date' in response_data['data']['errors'])
        self.assertTrue('end_date' in response_data['data']['errors'])
        self.assertTrue('license_fee' in response_data['data']['errors'])

        request_data = {
            'start_date': '2015-11-10',
            'end_date': '2015-11-20',
            'amount': '5000',
            'license_fee': '10%',
            'comment': 'TESTCASE_PUT'
        }

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data),
                                       content_type='application/json')

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse('amount' in response_data['data']['errors'])
        self.assertTrue('start_date' in response_data['data']['errors'])
        self.assertFalse('end_date' in response_data['data']['errors'])
        self.assertFalse('license_fee' in response_data['data']['errors'])

        request_data['start_date'] = '2015-11-11'
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data),
                                       content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        item_id = response_data['data']

        item = models.CreditLineItem.objects.get(comment='TESTCASE_PUT')
        self.assertEqual(item.pk, item_id)


class AccountCreditItemViewTest(BCMViewTestCase):

    def test_permissions(self):
        url = reverse('accounts_credit_item', kwargs={
            'account_id': 1,
            'credit_id': 1,
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))
        response = self.client.delete(url)
        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url, json.dumps({}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        url = reverse('accounts_credit_item', kwargs={
            'account_id': 1,
            'credit_id': 1,
        })

        self.add_permission('account_credit_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        response_item = json.loads(response.content)['data']
        self.assertEqual(response_item, {
            "comment": u"Test case",
            "account_id": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "created_on": "2014-06-04",
            "created_by": "ziga.stopinsek@zemanta.com",
            "license_fee": "20%",
            "id": 1,
            "is_signed": False,
            "is_canceled": False,
            "amount": 100000,
            "budgets": [
                {
                    "campaign": "test campaign 1",
                    "end_date": "2015-11-30",
                    "spend": "0.0000",
                    "id": 1,
                    "total": "100000.0000",
                    "comment": "Test case",
                    "start_date": "2015-10-01"
                }
            ]
        })

    def test_delete(self):
        url = reverse('accounts_credit_item', kwargs={
            'account_id': 3,
            'credit_id': 2,
        })

        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))

        self.add_permission('account_credit_view')

        url = reverse('accounts_credit_item', kwargs={
            'account_id': 3,
            'credit_id': 2,
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(pk=2)))

    def test_post(self):
        url = reverse('accounts_credit_item', kwargs={
            'account_id': 3,
            'credit_id': 2,
        })

        data = {}
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, 401)

        self.add_permission('account_credit_view')

        item = models.CreditLineItem.objects.get(pk=2)
        self.assertEqual(item.amount, 100000)

        data = {
            'start_date': '2015-12-01',
            'end_date': '2015-12-01',
            'amount': '1000',
            'license_fee': '30%',
            'comment': 'no comment',
            'account': 3,
        }
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, json.dumps(data), content_type='application/json')

        item = models.CreditLineItem.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(item.amount, 1000)
        self.assertEqual(json.loads(response.content)['data'], "2")


class CampaignBudgetViewTest(BCMViewTestCase):

    def test_get(self):
        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)['data']

        self.assertEqual(data, {
            "active": [
                {
                    "available": "100000.0000",
                    "is_editable": False,
                    "is_updatable": True,
                    "state": 1,
                    "end_date": "2015-11-30",
                    "license_fee": "20%",
                    "total": "100000.0000",
                    "spend": "0.0000",
                    "id": 1,
                    "comment": "Test case",
                    "start_date": "2015-10-01",
                }
            ],
            "past": [],
            "credits": [
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "id": 1,
                    "is_available": False,
                    "comment": "Test case",
                    "license_fee": "20",
                    "total": "100000.0000",
                    "start_date": "2015-10-01"
                }
            ],
            u"min_amount": 0,
            "totals": {
                "current": {
                    "available": "100000.0000",
                    "past": "0.0000",
                    "unallocated": "0.0000"
                },
                "lifetime": {
                    "data_spend": "0.0000",
                    "campaign_spend": "0.0000",
                    "media_spend": "0.0000",
                    "license_fee": "0.0000"
                }
            }
        })

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 11)
            response = self.client.get(url)

        data = json.loads(response.content)['data']
        self.assertEqual(data, {
            "active": [
                {
                    "available": "100000.0000",
                    "is_editable": True,
                    "is_updatable": False,
                    "state": 2,
                    "end_date": "2015-11-30",
                    "license_fee": "20%",
                    "total": "100000.0000",
                    "spend": "0.0000",
                    "id": 1,
                    "comment": "Test case",
                    "start_date": "2015-10-01",
                }
            ],
            "past": [],
            "credits": [
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "id": 1,
                    "is_available": False,
                    "comment": "Test case",
                    "license_fee": "20",
                    "total": "100000.0000",
                    "start_date": "2015-10-01"
                }
            ],
            "min_amount": 0,
            "totals": {
                "current": {
                    "available": "100000.0000",
                    "past": "0.0000",
                    "unallocated": "0.0000"
                },
                "lifetime": {
                    "data_spend": "0.0000",
                    "campaign_spend": "0.0000",
                    "media_spend": "0.0000",
                    "license_fee": "0.0000"
                }
            }
        })

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    def test_put(self, mock_lmode):
        mock_lmode.return_value = False
        data = {
            'credit': 2,
            'amount': '1000',
            'start_date': '2015-10-01',
            'end_date': '2015-12-31',
            'comment': 'Comment'
        }

        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data['start_date'] = '2015-12-01'
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        credit = models.CreditLineItem.objects.get(pk=2)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_lmode.called)

        insert_id = int(json.loads(response.content)['data'])
        self.assertEqual(models.BudgetLineItem.objects.get(pk=insert_id).comment, 'Comment')


class CampaignBudgetItemViewTest(BCMViewTestCase):

    def test_get(self):
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)['data'],
            {
                "comment": "Test case",
                "is_editable": False,
                "is_updatable": True,
                "amount": 100000,
                "end_date": "2015-11-30",
                "state": 1,
                "created_at": "2014-06-04T05:58:21",
                "credit": {
                    "license_fee": "0.2000",
                    "id": 1,
                    "name": "1 - test account 1 - $100000 - from 2015-10-01 to 2015-11-30",
                },
                "start_date": "2015-10-01",
                "created_by": "ziga.stopinsek@zemanta.com"
            }
        )

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    def test_post(self, mock_lmode):
        data = {}
        mock_lmode.return_value = False
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {
            'credit': 1,
            'start_date': '2015-10-01',
            'end_date': '2015-11-30',
            'amount': 1000,
            'comment': 'Test case test_post',
        }
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 400)

        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)['data'],
            {'id': 1, 'state_changed': False}
        )
        self.assertTrue(mock_lmode.called)
        self.assertEqual(models.BudgetLineItem.objects.get(pk=1).comment, 'Test case test_post')

        mock_lmode.return_value = True
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)['data'],
            {'id': 1, 'state_changed': True}
        )

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    @patch('automation.campaign_stop.is_current_time_valid_for_amount_editing')
    @patch('automation.campaign_stop.get_minimum_budget_amount')
    def test_post_lower_unactive(self, mock_min_amount, mock_valid_time, mock_lmode):
        mock_lmode.return_value = False
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        mock_min_amount.return_value = Decimal('80000.0000')
        mock_valid_time.return_value = True
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })
        data = {
            'credit': 1,
            'start_date': '2015-10-01',
            'end_date': '2015-11-30',
            'amount': 90000,
            'comment': 'Test case test_post',
        }
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)  # before start date
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertTrue(mock_min_amount.called)
        self.assertTrue(mock_valid_time.called)
        self.assertEqual(response.status_code, 200)

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    @patch('automation.campaign_stop.is_current_time_valid_for_amount_editing')
    @patch('automation.campaign_stop.get_minimum_budget_amount')
    def test_post_lower_active(self, mock_min_amount, mock_valid_time, mock_lmode):
        mock_lmode.return_value = False
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        mock_min_amount.return_value = Decimal('80000.0000')
        mock_valid_time.return_value = True
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })
        data = {
            'credit': 1,
            'start_date': '2015-10-01',
            'end_date': '2015-11-30',
            'amount': 90000,
            'comment': 'Test case test_post',
        }

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertTrue(mock_min_amount.called)
        self.assertTrue(mock_valid_time.called)
        self.assertEqual(response.status_code, 200)

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    @patch('automation.campaign_stop.is_current_time_valid_for_amount_editing')
    @patch('automation.campaign_stop.get_minimum_budget_amount')
    def test_post_lower_active_too_low(self, mock_min_amount, mock_valid_time, mock_lmode):
        mock_lmode.return_value = False
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        mock_min_amount.return_value = Decimal('95000.0000')
        mock_valid_time.return_value = True
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })
        data = {
            'credit': 1,
            'start_date': '2015-10-01',
            'end_date': '2015-11-30',
            'amount': 90000,
            'comment': 'Test case test_post',
        }

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertTrue(mock_min_amount.called)
        self.assertTrue(mock_valid_time.called)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data['data']['errors']['amount'],
            ['Budget exceeds the minimum budget amount by $5000.00.']
        )

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    @patch('automation.campaign_stop.is_current_time_valid_for_amount_editing')
    @patch('automation.campaign_stop.get_minimum_budget_amount')
    def test_post_lower_active_invalid_time(self, mock_min_amount, mock_valid_time, mock_lmode):
        mock_lmode.return_value = False
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        mock_min_amount.return_value = Decimal('80000.0000')
        mock_valid_time.return_value = False
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })
        data = {
            'credit': 1,
            'start_date': '2015-10-01',
            'end_date': '2015-11-30',
            'amount': '90000',
            'comment': 'Test case test_post',
        }

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 30)
            response = self.client.post(url, json.dumps(data),
                                        content_type='application/json')
        self.assertTrue(mock_min_amount.called)
        self.assertTrue(mock_valid_time.called)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data['data']['errors']['amount'],
            ['You cannot lower the amount on an active budget line item at this time.']
        )

    @patch('automation.campaign_stop.check_and_switch_campaign_to_landing_mode')
    def test_delete(self, mock_lmode):
        mock_lmode.return_value = False
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2016, 1, 1)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_lmode.called)


class BudgetSpendInViewsTestCase(BCMViewTestCase):

    def test_active_budget(self):
        today = datetime.date(2015, 11, 11)

        budget = models.BudgetLineItem.objects.get(pk=1)
        budget.credit.amount = 250000
        budget.credit.status = constants.CreditLineItemStatus.SIGNED
        budget.credit.save()
        BudgetDailyStatement.objects.create(
            budget=budget,
            date=today,
            media_spend_nano=300 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=200 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=50 * models.TO_NANO_MULTIPLIER,
        )

        # Another budget with daily statement
        budget.pk = None
        budget.total = 50000
        budget.save()
        BudgetDailyStatement.objects.create(
            budget=budget,
            date=today,
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=105 * (10**8),
        )

        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = today
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']

        self.assertEqual(data, {
            "active": [
                {
                    u"available": u"99789.5000",
                    u"is_editable": False,
                    u"is_updatable": True,
                    u"state": 1,
                    u"end_date": u"2015-11-30",
                    u"license_fee": u"20%",
                    u"total": "100000.0000",
                    u"spend": u"210.5000",
                    u"id": 2,
                    u"comment": u"Test case",
                    u"start_date": u"2015-10-01",
                },
                {
                    u"available": u"99450.0000",
                    u"is_editable": False,
                    u"is_updatable": True,
                    u"state": 1,
                    u"end_date": u"2015-11-30",
                    u"license_fee": u"20%",
                    u"total": "100000.0000",
                    u"spend": u"550.0000",
                    u"id": 1,
                    u"comment": u"Test case",
                    u"start_date": u"2015-10-01",
                }
            ],
            u"min_amount": 0,
            u"past": [],
            u"credits": [
                {
                    u"available": u"50000.0000",
                    u"end_date": u"2015-11-30",
                    u"id": 1,
                    u"is_available": True,
                    u"license_fee": u"20",
                    u"comment": "Test case",
                    u"total": "250000.0000",
                    u"start_date": u"2015-10-01"
                }
            ],
            u"totals": {
                u"current": {
                    u"available": u"199239.5000",
                    u"past": u"0.0000",
                    u"unallocated": u"50000.0000"
                },
                u"lifetime": {
                    u"data_spend": u"300.0000",
                    u"campaign_spend": u"760.5000",
                    u"media_spend": u"400.0000",
                    u"license_fee": u"60.5000",
                }
            }
        })


class BudgetReserveInViewsTestCase(BCMViewTestCase):

    def test_credit_view(self):
        url = reverse('accounts_credit', kwargs={'account_id': 1})
        today = datetime.date(2015, 11, 11)

        self.add_permission('account_credit_view')

        credit = models.CreditLineItem.objects.create(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal('0.2'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget = models.BudgetLineItem.objects.create(
            credit=credit,
            amount=10000,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )

        BudgetDailyStatement.objects.create(
            budget=budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=500 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=50 * models.TO_NANO_MULTIPLIER,
        )
        for num in range(0, 5):
            BudgetDailyStatement.objects.create(
                budget=budget,
                date=today + datetime.timedelta(num),
                media_spend_nano=800 * models.TO_NANO_MULTIPLIER,
                data_spend_nano=0,
                license_fee_nano=80 * models.TO_NANO_MULTIPLIER,
            )

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = today
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content)['data'], {
            "active": [
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "created_on": str(budget.created_dt.date()),
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": "10000.0000",
                    "total": "10000.0000",
                    "id": 3,
                    "is_signed": True,
                    "is_canceled": False,
                    "comment": None,
                    "budgets": [
                        {"amount": 10000, "id": 2}
                    ],
                    "start_date": "2015-11-01"
                },
                {
                    "available": "0.0000",
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": "100000.0000",
                    "comment": "Test case",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "past": [],
            "totals": {
                "available": "0.0000",
                "allocated": "110000.0000",
                "total": "110000.0000",
                "past": "0",
            }
        })

        on_reserve_data = {
            "active": [
                {
                    "available": "5006.0000",
                    "end_date": "2015-11-30",
                    "created_on": str(budget.created_dt.date()),
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "comment": None,
                    "allocated": "4994.0000",
                    "total": "10000.0000",
                    "id": 3,
                    "is_signed": True,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 10000, "id": 2}
                    ],
                    "start_date": "2015-11-01"
                },
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "comment": "Test case",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "past": [],
            "totals": {
                "available": "5006.0000",
                "allocated": "104994.0000",
                "total": "110000.0000",
                "past": "0",
            }
        }
        on_freed_data = {
            "active": [
                {
                    "available": "5050.0000",
                    "end_date": "2015-11-30",
                    "created_on": str(budget.created_dt.date()),
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": "4950.0000",
                    "comment": None,
                    "total": "10000.0000",
                    "id": 3,
                    "is_signed": True,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 10000, "id": 2}
                    ],
                    "start_date": "2015-11-01"
                },
                {
                    "available": "0.0000",
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "comment": "Test case",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "past": [],
            "totals": {
                "available": "5050.0000",
                "allocated": "104950.0000",
                "total": "110000.0000",
                "past": "0",
            }
        }

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)['data'], on_reserve_data)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 12)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)['data'], on_reserve_data)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 13)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)['data'], on_reserve_data)

        # After sync time has passed
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 14)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)['data'], on_freed_data)
