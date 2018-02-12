import json
from mock import patch

from dash import constants
from dash import models

from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.test import Client, TestCase, override_settings

from utils import test_helper
from utils import s3helpers
from zemauth.models import User


class PublisherTargetingViewTest(TestCase):
    fixtures = ['test_publishers.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def get_payload(self, **kwargs):
        payload = {
            'entries': [{
                'publisher': 'cnn.com',
            }],
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
        }
        payload.update(kwargs)
        return payload

    def assertEntriesInserted(self, publisher_group):
        entry_dicts = [{
            'publisher': 'cnn.com',
            'source': None,
            'include_subdomains': False,
        }]
        self.assertEqual(publisher_group.entries.count(), len(entry_dicts))
        entries = publisher_group.entries.all().values('publisher', 'source', 'include_subdomains')
        self.assertCountEqual(entry_dicts, entries)

    def test_post_not_allowed(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        payload = self.get_payload(ad_group=ad_group.id)

        response = self.client.post(
            reverse('publisher_targeting'), data=payload)
        self.assertEqual(response.status_code, 404)

    def test_post_ad_group(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status'
        ])
        payload = self.get_payload(ad_group=ad_group.id)

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEntriesInserted(ad_group.default_blacklist)

    def test_post_campaign_not_allowed(self):
        campaign = models.Campaign.objects.get(pk=1)
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status'
        ])
        payload = self.get_payload(campaign=campaign.id)

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_post_campaign(self):
        campaign = models.Campaign.objects.get(pk=1)
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status',
            'can_access_campaign_account_publisher_blacklist_status',
        ])
        payload = self.get_payload(campaign=campaign.id)

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        campaign.refresh_from_db()
        self.assertEntriesInserted(campaign.default_blacklist)

    def test_post_account_not_allowed(self):
        account = models.Account.objects.get(pk=1)
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status'
        ])
        payload = self.get_payload(account=account.id)

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_post_account(self):
        account = models.Account.objects.get(pk=1)
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status',
            'can_access_campaign_account_publisher_blacklist_status',
        ])
        payload = self.get_payload(account=account.id)

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEntriesInserted(account.default_blacklist)

    def test_post_global_not_allowed(self):
        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status'
        ])
        payload = self.get_payload()

        response = self.client.post(
            reverse('publisher_targeting'),
            data=json.dumps(payload),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_post_global(self):
        global_group = models.PublisherGroup(name='imglobal')
        request = HttpRequest()
        request.user = self.user
        global_group.save(request)

        test_helper.add_permissions(self.user, [
            'can_modify_publisher_blacklist_status',
            'can_access_global_publisher_blacklist_status',
        ])
        payload = self.get_payload()

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            response = self.client.post(
                reverse('publisher_targeting'),
                data=json.dumps(payload),
                content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEntriesInserted(global_group)


class PublisherGroupsViewTest(TestCase):

    fixtures = ['test_publishers.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_get_not_allowed(self):
        response = self.client.get(
            reverse('accounts_publisher_groups', kwargs={'account_id': 1}))
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])
        account = models.Account.objects.get(pk=1)

        response = self.client.get(
            reverse('accounts_publisher_groups', kwargs={'account_id': account.id}))

        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        for pg in content['data']['publisher_groups']:
            # check user has permission for all the publisher groups returned
            self.assertEqual(models.PublisherGroup.objects.filter(pk=pg['id']).filter_by_account(account).count(), 1)

    def test_get_not_implicit(self):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])
        account = models.Account.objects.get(pk=1)

        response = self.client.get(
            reverse('accounts_publisher_groups', kwargs={'account_id': account.id}), data={
                'not_implicit': True,
            })

        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        for pg in content['data']['publisher_groups']:
            # check user has permission for all the publisher groups returned
            pgs = models.PublisherGroup.objects.filter(pk=pg['id']).filter_by_account(account)
            self.assertEqual(pgs.count(), 1)
            self.assertFalse(pgs.first().implicit)


class PublisherGroupsUploadTest(TestCase):

    fixtures = ['test_publishers.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_get_not_allowed(self):
        response = self.client.get(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': 1, 'csv_key': 'asd'}))
        self.assertEqual(response.status_code, 404)

    def test_post_not_allowed(self):
        response = self.client.post(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': 1}))
        self.assertEqual(response.status_code, 404)

    @patch.object(s3helpers.S3Helper, 'get')
    def test_get(self, mock_s3):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])

        response = self.client.get(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': 1, 'csv_key': 'asd'}))

        self.assertEqual(response.status_code, 200)
        mock_s3.assert_called_with('publisher_group_errors/account_1/asd.csv')

    def test_post_update(self):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])
        account = models.Account.objects.get(pk=1)
        data = {
            'id': 1,
            'name': 'qweasd',
            'include_subdomains': True,
        }

        response = self.client.post(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': account.id}),
            data=data)

        self.assertEqual(response.status_code, 200)
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        self.assertEqual(publisher_group.name, 'qweasd')
        for entry in publisher_group.entries.all():
            self.assertEqual(entry.include_subdomains, True)

    def test_post_update_apply_include_subdomains(self):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])
        account = models.Account.objects.get(pk=1)
        data = {
            'id': 1,
            'name': 'qweasd',
            'include_subdomains': False,
        }

        response = self.client.post(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': account.id}),
            data=data)

        self.assertEqual(response.status_code, 200)
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        self.assertEqual(publisher_group.name, 'qweasd')
        for entry in publisher_group.entries.all():
            self.assertEqual(entry.include_subdomains, False)

    def test_post_create(self):
        test_helper.add_permissions(self.user, ['can_edit_publisher_groups'])
        account = models.Account.objects.get(pk=1)
        mock_file = test_helper.mock_file('asd.csv', """\
        Publisher,Source
        asd,
        qwe,adsnative""")
        data = {
            'name': 'qweasd',
            'include_subdomains': True,
            'entries': mock_file,
        }

        response = self.client.post(
            reverse('accounts_publisher_groups_upload', kwargs={'account_id': account.id}),
            data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response['data']['name'], 'qweasd')

        publisher_group = models.PublisherGroup.objects.get(pk=response['data']['id'])
        self.assertEqual(publisher_group.name, 'qweasd')
        for entry in publisher_group.entries.all():
            self.assertEqual(entry.include_subdomains, True)
