import mock

from django.contrib.auth import models as authmodels
from django.db import IntegrityError
from django.test import TestCase

from dash import models as dashmodels
from zemauth.models import User


class TestDashSignals(TestCase):

    fixtures = ['test_signals.yaml']

    def _prepare_mock_get_request(self, mock_get_request):
        mock_request = mock.Mock()
        mock_request.user = User.objects.get(username='tomaz')
        mock_get_request.return_value = mock_request

    def test_account_no_request_available(self):
        with self.assertRaises(IntegrityError):
            dashmodels.Account(name='test account name').save()

    @mock.patch('utils.signal_handlers.get_request')
    def test_account_request_available(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)
        dashmodels.Account(name='test account name 2').save()
        self.assertEqual(
            dashmodels.Account.objects.get(name='test account name 2').modified_by.username,
            'tomaz',
        )

    def test_campaign_no_request_available(self):
        account = dashmodels.Account.objects.get(pk=1)
        with self.assertRaises(IntegrityError):
            dashmodels.Campaign(name='test campaign name', account=account).save()

    @mock.patch('utils.signal_handlers.get_request')
    def test_campaign_request_available(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)
        account = dashmodels.Account.objects.get(pk=1)
        dashmodels.Campaign(name='test campaign name 2', account=account).save()
        self.assertEqual(
            dashmodels.Campaign.objects.get(
                name='test campaign name 2',
                account=account,
            ).modified_by.username,
            'tomaz',
        )

    def test_adgroup_no_request_available(self):
        campaign = dashmodels.Campaign.objects.get(pk=1)
        with self.assertRaises(IntegrityError):
            dashmodels.AdGroup(name='test adgroup name', campaign=campaign).save()

    @mock.patch('utils.signal_handlers.get_request')
    def test_adgroup_request_available(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)
        campaign = dashmodels.Campaign.objects.get(pk=1)

        dashmodels.AdGroup(name='test adgroup name 2', campaign=campaign).save()
        self.assertEqual(
            dashmodels.AdGroup.objects.get(name='test adgroup name 2').modified_by.username,
            'tomaz',
        )

    def test_adgroup_settings_no_request_available(self):
        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        with self.assertRaises(IntegrityError):
            dashmodels.AdGroupSettings(ad_group=ad_group).save()

    @mock.patch('utils.signal_handlers.get_request')
    def test_adgroup_settings_request_available(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)
        ad_group = dashmodels.AdGroup.objects.get(pk=1)

        settings = dashmodels.AdGroupSettings(ad_group=ad_group)
        settings.save()
        self.assertEqual(settings.created_by.username, 'tomaz')

    def test_adgroup_source_settings_no_request_available(self):
        dashmodels.AdGroupSourceSettings().save()
        self.assertEqual(dashmodels.AdGroupSourceSettings.objects.latest().created_by, None)

    @mock.patch('utils.signal_handlers.get_request')
    def test_adgroup_source_settings_request_available(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)

        settings = dashmodels.AdGroupSourceSettings()
        settings.save()
        self.assertEqual(settings.created_by.username, 'tomaz')

    @mock.patch('utils.signal_handlers.get_request')
    def test_group_account_automatically_add(self, mock_get_request):
        self._prepare_mock_get_request(mock_get_request)

        perm = authmodels.Permission.objects.get(
            codename='group_account_automatically_add')
        group = authmodels.Group.objects.get(pk=1)
        group.permissions.add(perm)
        group.save()

        # This is here just to make sure that there are at least 2 groups in the database
        # because only 1 will have access to the new account.
        group2 = authmodels.Group.objects.get(pk=2)
        self.assertTrue(group2)

        account = dashmodels.Account(name='New Account')
        account.save()

        self.assertEqual([x.pk for x in account.groups.all()], [1])

        # Make sure that existing accounts are not automatically added to the group.
        existing_account = dashmodels.Account.objects.get(pk=1)
        existing_account.name = 'existing test account 1'
        existing_account.save()

        self.assertEqual([x.pk for x in existing_account.groups.all()], [])
