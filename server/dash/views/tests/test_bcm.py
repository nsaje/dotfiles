#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.test import TestCase

from zemauth.models import User
from dash import models

class BCMViewTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

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
                    "available": 0,
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": 100000,
                    "total": 100000,
                    "id": 1,
                    "is_signed": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "past": [],
            "totals": {
                "available": "0",
                "allocated": "100000",
                "total": "100000",
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
                    "available": 0,
                    "end_date":
                    "2015-11-30",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "allocated": 100000,
                    "total": 100000,
                    "id": 1,
                    "is_signed": False,
                    "budgets": [
                        {"amount": 100000, "id": 1}
                    ],
                    "start_date": "2015-10-01"
                }
            ],
            "totals": {
                "available": "0",
                "allocated": "0",
                "past": "100000",
                "total": "100000"
            }
        })

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
            "amount": 100000,
            "budgets": [
                {
                    "campaign": "test campaign 1",
                    "end_date": "2015-11-30",
                    "spend": "0",
                    "id": 1,
                    "total": 100000,
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
    def test_permissions(self):
        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 401)
    
    def test_get(self):
        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        self.add_permission('campaign_budget_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)['data']

        self.assertEqual(data, {
            "active": [
                {
                    "available": "100000",
                    "is_editable": False,
                    "is_updatable": True,
                    "state": 1,
                    "end_date": "2015-11-30",
                    "license_fee": "20%",
                    "total": 100000,
                    "spend": "0",
                    "id": 1,
                    "comment": "Test case",
                    "start_date": "2015-10-01",
                }
            ],
            "past": [],
            "credits": [
                {
                    "available": 0,
                    "end_date": "2015-11-30",
                    "id": 1,
                    "is_available": False,
                    "license_fee": "20",
                    "total": 100000,
                    "start_date": "2015-10-01"
                }
            ],
            "totals": {
                "current": {
                    "available": "0",
                    "past": "0",
                    "unallocated": "0"
                },
                "lifetime": {
                    "data_spend": "0",
                    "campaign_spend": "0",
                    "media_spend": "0",
                    "license_fee": "0"
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
                    "available": "100000",
                    "is_editable": True,
                    "is_updatable": False,
                    "state": 2,
                    "end_date": "2015-11-30",
                    "license_fee": "20%",
                    "total": 100000,
                    "spend": "0",
                    "id": 1,
                    "comment": "Test case",
                    "start_date": "2015-10-01",
                }
            ],
            "past": [],
            "credits": [
                {
                    "available": 0,
                    "end_date": "2015-11-30",
                    "id": 1,
                    "is_available": False,
                    "license_fee": "20",
                    "total": 100000,
                    "start_date": "2015-10-01"
                }
            ],
            "totals": {
                "current": {
                    "available": "0",
                    "past": "0",
                    "unallocated": "0"
                },
                "lifetime": {
                    "data_spend": "0",
                    "campaign_spend": "0",
                    "media_spend": "0",
                    "license_fee": "0"
                }
            }
        })

    def test_put(self):
        data = {
            'credit': 2,
            'amount': '1000',
            'start_date': '2015-10-01',
            'end_date': '2015-12-31',
            'comment': 'Comment'
        }
        
        url = reverse('campaigns_budget', kwargs={'campaign_id': 1})

        self.add_permission('campaign_budget_view')
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

        insert_id = int(json.loads(response.content)['data'])
        self.assertEqual(models.BudgetLineItem.objects.get(pk=insert_id).comment, 'Comment')
        

class CampaignBudgetItemViewTest(BCMViewTestCase):
    def test_permissions(self):
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url, json.dumps({}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 401)

        
    def test_get(self):
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        self.add_permission('campaign_budget_view')
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
                    "name": "test account 1 - $100000 - from 2015-10-01 to 2015-11-30",
                },
                "start_date": "2015-10-01",
                "created_by": "ziga.stopinsek@zemanta.com"
            }
        )


    def test_post(self):
        data = {}
        
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        self.add_permission('campaign_budget_view')
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
        self.assertEqual(models.BudgetLineItem.objects.get(pk=1).comment, 'Test case test_post')

    def test_delete(self):
        url = reverse('campaigns_budget_item', kwargs={
            'campaign_id': 1,
            'budget_id': 1,
        })

        self.add_permission('campaign_budget_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2016, 1, 1)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

        self.add_permission('campaign_budget_view')
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
