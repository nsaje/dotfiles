from rest_framework.test import APIClient
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
import mock

from zemauth.models import User
import core.entity
import dash.constants
from . import service

from utils.magic_mixer import magic_mixer


class CreateClientTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        magic_mixer.blend(User, email=service.DEFAULT_CS_REPRESENTATIVE)
        magic_mixer.blend(User, email=service.DEFAULT_SALES_REPRESENTATIVE)

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
        self.assertEqual(client.cs_representative.email, service.DEFAULT_CS_REPRESENTATIVE)
        self.assertEqual(client.sales_representative.email, service.DEFAULT_SALES_REPRESENTATIVE)

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
        sett = client.get_current_settings()
        self.assertEqual(sett.account_type, dash.constants.AccountType.TEST)
        self.assertEqual(sett.default_cs_representative.email, service.DEFAULT_CS_REPRESENTATIVE)
        self.assertEqual(sett.default_sales_representative.email, service.DEFAULT_SALES_REPRESENTATIVE)

    def test_put_invalid(self):
        url = reverse('service.salesforce.client')

        data = {
            'salesforceAccountId': 1,
            'type': 'agency',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {'name': ['This field is required.']},
            'errorCode': 'ValidationError'
        })

        data = {
            'salesforceAccountId': 1,
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {'type': ['This field is required.']},
            'errorCode': 'ValidationError'
        })

        data = {
            'type': 'brand',
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)

        self.assertEqual(r.json(), {
            'details': {'salesforceAccountId': ['This field is required.']},
            'errorCode': 'ValidationError',
        })

        data = {
            'salesforceAccountId': 1,
            'type': 'invalid-type',
            'name': 'Some name',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {
            'details': {'type': ['"invalid-type" is not a valid choice.']},
            'errorCode': 'ValidationError',
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
            'details': {'name': 'Name is not unique for this account type.'},
            'errorCode': 'ValidationError',
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
                'amountAtSigning': ['This field is required.'],
                'contractNumber': ['This field is required.'],
                'description': ['This field is required.'],
                'endDate': ['This field is required.'],
                'pfSchedule': ['This field is required.'],
                'salesforceAccountId': ['This field is required.'],
                'salesforceContractId': ['This field is required.'],
                'startDate': ['This field is required.'],
                'z1_accountId': ['This field is required.'],
            },
            'errorCode': 'ValidationError',
        })

    def test_invalid_fields(self):
        url = reverse('service.salesforce.credit')

        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'endDate': '2017-05-10',
            'startDate': '2017-06-20',
            'pfSchedule': 'bla',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'c1',
            'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            'details': {'pfSchedule': ['"bla" is not a valid choice.']},
            'errorCode': 'ValidationError'
        })

    def test_missing_fee(self):
        url = reverse('service.salesforce.credit')

        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'startDate': '2017-05-10',
            'endDate': '2017-06-20',
            'pfSchedule': 'monthly as used',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'a1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            'details': {'nonFieldErrors': ['Fee not provided']},
            'errorCode': 'ValidationError',
        })

    def test_invalid_account(self):
        url = reverse('service.salesforce.credit')
        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'startDate': '2017-05-10',
            'endDate': '2017-06-20',
            'pfSchedule': 'monthly as used',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': '10',
            'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        self.assertEqual(r.json(), {
            'details': {'z1_accountId': 'Invalid format'},
            'errorCode': 'ValidationError',
        })

    @mock.patch('core.bcm.bcm_slack.log_to_slack')
    def test_create_agency_credit(self, mock_slack):
        url = reverse('service.salesforce.credit')

        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'startDate': '2017-05-10',
            'endDate': '2017-06-20',
            'pfSchedule': 'monthly as used',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'a1',
            'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_cliId': cli.pk,
                'z1_data': {
                    'amount': 500.0,
                    'comment': 'Some description',
                    'startDate': '2017-05-10',
                    'flatFeeCc': 0,
                    'flatFeeEndDate': None,
                    'flatFeeStartDate': None,
                    'licenseFee': 0.1,
                    'endDate': '2017-06-20',
                    'status': 1
                }
            }
        })
        mock_slack.assert_called_with(
            None,
            'New agency credit #{} added to agency {} with amount $500 and end date 2017-06-20.'.format(
                cli.pk,
                self.agency.name
            )
        )

    @mock.patch('core.bcm.bcm_slack.log_to_slack')
    def test_create_account_credit(self, mock_slack):
        url = reverse('service.salesforce.credit')
        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'startDate': '2017-05-10',
            'endDate': '2017-06-20',
            'pfSchedule': 'monthly as used',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'b1',
            'pct_of_budget': '0.1',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_cliId': cli.pk,
                'z1_data': {
                    'amount': 500.0,
                    'comment': 'Some description',
                    'startDate': '2017-05-10',
                    'flatFeeCc': 0,
                    'flatFeeEndDate': None,
                    'flatFeeStartDate': None,
                    'licenseFee': 0.1,
                    'endDate': '2017-06-20',
                    'status': 1
                }
            }
        })
        mock_slack.assert_called_with(
            1,
            'New credit #{} added on account <https://one.zemanta.com/v2/credit/account/1|{}> with amount $500 and end date 2017-06-20.'.format(
                cli.pk,
                self.account.get_long_name()
            ),
        )

    @mock.patch('core.bcm.bcm_slack.log_to_slack')
    def test_flat_fee_upfront(self, mock_slack):
        url = reverse('service.salesforce.credit')
        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'endDate': '2017-06-20',
            'startDate': '2017-05-10',
            'pfSchedule': 'upon execution of this agreement',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'b1',
            'calc_variable_fee': '100.0',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_cliId': cli.pk,
                'z1_data': {
                    'amount': 500.0,
                    'comment': 'Some description',
                    'endDate': '2017-06-20',
                    'flatFeeCc': 1000000,
                    'flatFeeEndDate': '2017-05-10',
                    'flatFeeStartDate': '2017-05-10',
                    'licenseFee': 0.0,
                    'startDate': '2017-05-10',
                    'status': 1
                }
            }
        })
        mock_slack.assert_called_with(
            1,
            'New credit #{} added on account <https://one.zemanta.com/v2/credit/account/1|{}> with amount $500 and end date 2017-06-20.'.format(
                cli.pk,
                self.account.get_long_name()
            ),
        )

    @mock.patch('core.bcm.bcm_slack.log_to_slack')
    def test_flat_fee(self, mock_slack):
        url = reverse('service.salesforce.credit')
        data = {
            'amountAtSigning': '500.0',
            'billingContract': 'contract',
            'contractNumber': '00',
            'description': 'Some description',
            'startDate': '2017-05-10',
            'endDate': '2017-06-20',
            'pfSchedule': 'monthly in installments',
            'salesforceAccountId': '123',
            'salesforceContractId': '111',
            'z1_accountId': 'b1',
            'calc_variable_fee': '100.0',
        }
        r = self.client.put(url, data=data, format='json')
        cli = core.bcm.credit_line_item.CreditLineItem.objects.all().order_by('-created_dt').first()
        self.assertEqual(r.json(), {
            'data': {
                'z1_cliId': cli.pk,
                'z1_data': {
                    'amount': 500.0,
                    'comment': 'Some description',
                    'startDate': '2017-05-10',
                    'flatFeeCc': 1000000,
                    'flatFeeEndDate': '2017-06-20',
                    'flatFeeStartDate': '2017-05-10',
                    'licenseFee': 0.0,
                    'endDate': '2017-06-20',
                    'status': 1
                }
            }
        })
        mock_slack.assert_called_with(
            1,
            'New credit #{} added on account <https://one.zemanta.com/v2/credit/account/1|{}> with amount $500 and end date 2017-06-20.'.format(
                cli.pk,
                self.account.get_long_name()
            ),
        )


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
            'data': [
                {'name': '#2 Acc 1', 'z1_accountId': 'b2'},
                {'name': '#3 Acc 2', 'z1_accountId': 'b3'}
            ]
        })

    def test_brand(self):
        magic_mixer.blend(core.entity.account.Account, agency_id=None, id=1, name='Acc 0').save(self.request_mock)

        url = reverse('service.salesforce.agency_accounts')
        r = self.client.post(url, data={
            'z1_accountId': 'b1'
        }, format='json')
        self.assertEqual(r.json(), {
            'details': {'z1_accountId': ['An agency account must be provided.']},
            'errorCode': 'ValidationError'
        })
