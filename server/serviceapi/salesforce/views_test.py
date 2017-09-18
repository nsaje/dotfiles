from rest_framework.test import APIClient
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse

from zemauth.models import User
import core.entity
import dash.constants

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
        client = core.entity.agency.Agency.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_accountId': client.get_salesforce_id(),
                'z1_data': 'Agency 1',
            },
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(client.default_account_type, dash.constants.AccountType.TEST)

    def test_put_valid_account(self):
        data = {
            'salesforceAccountId': 1,
            'name': 'Brand 1',
            'type': 'brand',
        }
        url = reverse('service.salesforce.client')
        r = self.client.put(url, data=data, format='json')
        client = core.entity.account.Account.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_accountId': client.get_salesforce_id(),
                'z1_data': 'Brand 1'
            },
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(client.get_current_settings().account_type, dash.constants.AccountType.TEST)

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

        magic_mixer.blend(core.entity.agency.Agency, name='Name exists')
        data = {
            'salesforceAccountId': 1,
            'type': 'agency',
            'name': 'Name exists',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            u'details': {u'name': u'Name is not unique for this account type.'},
            u'errorCode': u'ValidationError',
        })


class CreateCreditTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        self.account = magic_mixer.blend(core.entity.account.Account, id=1)
        self.agency = magic_mixer.blend(core.entity.agency.Agency, id=1)

    def test_missing_fields(self):
        url = reverse('service.salesforce.credit')

        data = {}
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            'details': {
                u'amountAtSigning': [u'This field is required.'],
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
            u'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            u'details': {u'pfSchedule': [u'"bla" is not a valid choice.']},
            u'errorCode': u'ValidationError'
        })

    def test_missing_fee(self):
        url = reverse('service.salesforce.credit')

        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'startDate': '2017-05-10',
            u'endDate': '2017-06-20',
            u'pfSchedule': 'monthly as used',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'a1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            u'details': {u'nonFieldErrors': [u'Fee not provided']},
            u'errorCode': u'ValidationError',
        })

    def test_create_agency_credit(self):
        url = reverse('service.salesforce.credit')

        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'startDate': '2017-05-10',
            u'endDate': '2017-06-20',
            u'pfSchedule': 'monthly as used',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'a1',
            u'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': cli.pk,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'startDate': u'2017-05-10',
                    u'flatFeeCc': 0,
                    u'flatFeeEndDate': None,
                    u'flatFeeStartDate': None,
                    u'licenseFee': 0.1,
                    u'endDate': u'2017-06-20',
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
            u'startDate': '2017-05-10',
            u'endDate': '2017-06-20',
            u'pfSchedule': 'monthly as used',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'b1',
            u'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': cli.pk,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'startDate': u'2017-05-10',
                    u'flatFeeCc': 0,
                    u'flatFeeEndDate': None,
                    u'flatFeeStartDate': None,
                    u'licenseFee': 0.1,
                    u'endDate': u'2017-06-20',
                    u'status': 1
                }
            }
        })

    def test_flat_fee_upfront(self):
        url = reverse('service.salesforce.credit')
        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'endDate': '2017-06-20',
            u'startDate': '2017-05-10',
            u'pfSchedule': 'upon execution of this agreement',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'b1',
            u'calc_variable_fee': '100.0',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': cli.pk,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'endDate': u'2017-06-20',
                    u'flatFeeCc': 1000000,
                    u'flatFeeEndDate': u'2017-05-10',
                    u'flatFeeStartDate': u'2017-05-10',
                    u'licenseFee': 0.0,
                    u'startDate': u'2017-05-10',
                    u'status': 1
                }
            }
        })

    def test_flat_fee(self):
        url = reverse('service.salesforce.credit')
        data = {
            u'amountAtSigning': '500.0',
            u'billingContract': 'contract',
            u'contractNumber': '00',
            u'description': 'Some description',
            u'startDate': '2017-05-10',
            u'endDate': '2017-06-20',
            u'pfSchedule': 'monthly in installments',
            u'salesforceAccountId': '123',
            u'salesforceContractId': '111',
            u'z1_accountId': 'b1',
            u'calc_variable_fee': '100.0',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            u'data': {
                u'z1_cliId': cli.pk,
                u'z1_data': {
                    u'amount': 500.0,
                    u'comment': u'Some description',
                    u'startDate': u'2017-05-10',
                    u'flatFeeCc': 1000000,
                    u'flatFeeEndDate': u'2017-06-20',
                    u'flatFeeStartDate': u'2017-05-10',
                    u'licenseFee': 0.0,
                    u'endDate': u'2017-06-20',
                    u'status': 1
                }
            }
        })


class AgencyAccountsTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        self.request_mock = RequestFactory()
        self.request_mock.user = self.user

    def test_valid(self):
        magic_mixer.blend(core.entity.agency.Agency, id=1, name='Agency 1').save(self.request_mock)
        magic_mixer.blend(core.entity.account.Account, agency_id=None, id=1, name='Acc 0').save(self.request_mock)
        magic_mixer.blend(core.entity.account.Account, agency_id=1, id=2, name='Acc 1').save(self.request_mock)
        magic_mixer.blend(core.entity.account.Account, agency_id=1, id=3, name='Acc 2').save(self.request_mock)

        url = reverse('service.salesforce.agency_accounts')
        r = self.client.post(url, data={
            'z1_accountId': 'a1'
        }, format='json')
        self.assertEqual(r.json(), {
            u'data': [
                {u'name': u'#2 Acc 1', u'z1_accountId': u'b2'},
                {u'name': u'#3 Acc 2', u'z1_accountId': u'b3'}
            ]
        })

    def test_brand(self):
        magic_mixer.blend(core.entity.account.Account, agency_id=None, id=1, name='Acc 0').save(self.request_mock)

        url = reverse('service.salesforce.agency_accounts')
        r = self.client.post(url, data={
            'z1_accountId': 'b1'
        }, format='json')
        self.assertEqual(r.json(), {
            u'details': {u'z1_accountId': [u'An agency account must be provided.']},
            u'errorCode': u'ValidationError'
        })
