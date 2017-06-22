from rest_framework.test import APIClient
from django.test import TestCase
from django.core.urlresolvers import reverse

from zemauth.models import User

from utils.magic_mixer import magic_mixer


class CreateClientTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

    def test_put_valid_agency(self):
        data = {
            'salesforceAccountId': 1,
            'name': 'Agency 1',
            'type': 'agency',
        }
        url = reverse('service.salesforce.client')
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            'data': {
                'z1_accountId': 'aNone',
                'z1_data': 'Agency Agency 1',
            },
        })

    def test_put_valid_account(self):
        data = {
            'salesforceAccountId': 1,
            'name': 'Brand 1',
            'type': 'brand',
        }
        url = reverse('service.salesforce.client')
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            'data': {
                'z1_accountId': 'bNone',
                'z1_data': 'Account Brand 1'
            },
        })

    def test_put_invalid(self):
        url = reverse('service.salesforce.client')

        data = {
            'salesforceAccountId': 1,
            'type': 'agency',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {u'name': [u'This field is required.']},
            u'errorCode': u'ValidationError'
        })

        data = {
            'salesforceAccountId': 1,
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {u'type': [u'This field is required.']},
            u'errorCode': u'ValidationError'
        })

        data = {
            'type': 'brand',
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)

        self.assertEqual(r.json(), {
            'details': {u'salesforceAccountId': [u'This field is required.']},
            u'errorCode': u'ValidationError',
        })

        data = {
            'salesforceAccountId': 1,
            'type': 'invalid-type',
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {u'type': [u'"invalid-type" is not a valid choice.']},
            u'errorCode': u'ValidationError',
        })


class CreateCreditTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)
        self.maxDiff = None

    def test_missing_fields(self):
        url = reverse('service.salesforce.credit')

        data = {}
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            'details': {
                u'amountAtSigning': [u'This field is required.'],
                u'billingContract': [u'This field is required.'],
                u'contractNumber': [u'This field is required.'],
                u'description': [u'This field is required.'],
                u'endDate': [u'This field is required.'],
                u'pfSchedule': [u'This field is required.'],
                u'salesforceAccountId': [u'This field is required.'],
                u'salesforceContractId': [u'This field is required.'],
                u'startDate': [u'This field is required.'],
                u'z1_accountId': [u'This field is required.'],
            },
            u'errorCode': u'ValidationError',
        })

    def test_invalid_fields(self):
        url = reverse('service.salesforce.credit')

        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'endDate': '2017-05-10',
            u'startDate': '2017-06-20',
            u'pfSchedule': 'bla',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'c1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            u'details': {u'pfSchedule': [u'"bla" is not a valid choice.']},
            u'errorCode': u'ValidationError'
        })

    def test_create_agency_credit(self):
        url = reverse('service.salesforce.credit')

        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'endDate': '2017-05-10',
            u'startDate': '2017-06-20',
            u'pfSchedule': 'pct',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'a1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': None,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'endDate': u'2017-05-10',
                    u'flatFeeCc': 0,
                    u'flatFeeEndDate': None,
                    u'flatFeeStartDate': None,
                    u'licenseFee': 0,
                    u'startDate': u'2017-06-20',
                    u'status': 1
                }
            }
        })

    def test_create_account_credit(self):
        url = reverse('service.salesforce.credit')
        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'endDate': '2017-05-10',
            u'startDate': '2017-06-20',
            u'pfSchedule': 'pct',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'b1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': None,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'endDate': u'2017-05-10',
                    u'flatFeeCc': 0,
                    u'flatFeeEndDate': None,
                    u'flatFeeStartDate': None,
                    u'licenseFee': 0,
                    u'startDate': u'2017-06-20',
                    u'status': 1
                }
            }
        })
