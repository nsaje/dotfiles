import json

from dash import constants
from dash import models

from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.test import Client, TestCase, override_settings

from utils import test_helper
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
        self.assertItemsEqual(entry_dicts, entries)

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
