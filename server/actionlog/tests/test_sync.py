import httplib
import mock
import datetime

from django.test import TestCase
from django.conf import settings
from django.http.request import HttpRequest

import dash.models
import actionlog.models
import zemauth.models

from actionlog import sync, constants

from utils.command_helpers import last_n_days
from utils import test_helper


class GlobalLastSuccessfulChildSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_success_by_child(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: None,
            4: utcnow,
        }, last_sync)

    def test_get_latest_success_by_child_none(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.save()

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(None, last_sync[1])

    def test_get_latest_success_by_child_deprecated(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])

    def test_get_latest_success_by_child_sources_filtered(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.save()

        last_sync = sync.GlobalSync(
            sources=dash.models.Source.objects.filter(id__in=[1, 2, 3, 4])
        ).get_latest_success_by_child()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_success_by_child_exclude_archived_account(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        acc = dash.models.Account.objects.get(id=2)
        acc.archive(r)

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: utcnow
        }, last_sync)

    def test_get_latest_success_by_child_exclude_archived_campaign(self):
        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        c = dash.models.Campaign.objects.get(id=2)
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__campaign=c):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(None, last_sync[1])

        c.archive(r)

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])

    def test_get_latest_success_by_child_exclude_archived_ad_group(self):
        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        ag = dash.models.AdGroup.objects.get(id=1)
        for ags in dash.models.AdGroupSource.objects.filter(ad_group=ag):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(None, last_sync[1])

        ag.archive(r)

        last_sync = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])


class GlobalLastSuccessfulSourceSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_get_latest_source_success(self):
        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual({
            1: None,
            2: None,
            3: None,
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
            7: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_last_source_success_deprecated(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual({
            1: None,
            2: None,
            3: None,
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
            7: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_last_souce_success_sources_filtered(self):
        last_sync = sync.GlobalSync(
            sources=dash.models.Source.objects.filter(id__in=[1, 2, 3])
        ).get_latest_source_success()
        self.assertEqual({
            1: None,
            2: None,
            3: None
        }, last_sync)

    def test_get_last_souce_success_archived_account(self):
        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        acc = dash.models.Account.objects.get(id=2)
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__campaign__account=acc):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(None, last_sync[1])
        self.assertEqual(None, last_sync[2])

        acc.archive(r)

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[2])

    def test_get_last_souce_success_archived_campaign(self):
        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        c1 = dash.models.Campaign.objects.get(id=3)
        c2 = dash.models.Campaign.objects.get(id=4)
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__campaign__in=[c1, c2]):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(None, last_sync[1])
        self.assertEqual(None, last_sync[2])

        c1.archive(r)
        c2.archive(r)

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[2])

    def test_get_last_souce_success_archived_ad_group(self):
        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')

        ad_groups = dash.models.AdGroup.objects.filter(id__in=[3, 4, 5, 7])
        for ags in dash.models.AdGroupSource.objects.filter(ad_group=ad_groups):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(None, last_sync[1])
        self.assertEqual(None, last_sync[2])

        for ag in ad_groups:
            ag.archive(r)

        last_sync = sync.GlobalSync().get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[1])
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[2])


class AccountLastSuccessfulChildSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.acc = dash.models.Account.objects.get(id=1)

    def test_get_latest_success_by_child(self):
        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_none(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.last_successful_sync_dt = None
        s.save()

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: None,
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_deprecated(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.last_successful_sync_dt = None
        s.save()

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_sources_filtered(self):
        sources = dash.models.Source.objects.filter(id__in=[1, 2, 3])
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = False
        s.last_successful_sync_dt = None
        s.save()

        last_sync = sync.AccountSync(self.acc, sources=sources).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_exclude_archived_campaign(self):
        c = dash.models.Campaign.objects.get(id=2)
        for ag in c.adgroup_set.all():
            for ags in ag.adgroupsource_set.all():
                ags.last_successful_sync_dt = None
                ags.save()

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: None
        }, last_sync)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        c.archive(r)

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_exclude_archived_ad_group(self):
        ag = dash.models.AdGroup.objects.get(id=1)
        for ags in ag.adgroupsource_set.all():
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: None,
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        ag.archive(r)

        last_sync = sync.AccountSync(self.acc).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_success_by_child_demo_account(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        acc = dash.models.Account.objects.get(id=4)
        last_sync = sync.AccountSync(acc).get_latest_success_by_child()
        self.assertEqual({
            6: utcnow,
        }, last_sync)


class AccountLastSuccessfulSourceSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.acc = dash.models.Account.objects.get(id=1)

    def test_get_latest_source_success(self):
        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
            7: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_latest_source_success_maintenance(self):
        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        s = dash.models.Source.objects.get(id=6)
        self.assertTrue(s.maintenance)

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_deprecated(self):
        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_sources_filtered(self):
        sources = dash.models.Source.objects.filter(id__in=[1, 2, 6])

        last_sync = sync.AccountSync(self.acc, sources=sources).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
        }, last_sync)

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_source_success_demo_account(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        acc = dash.models.Account.objects.get(id=4)

        last_sync = sync.AccountSync(acc).get_latest_source_success()
        self.assertEqual({
            1: utcnow,
            2: utcnow,
            3: utcnow,
            4: utcnow,
            5: utcnow,
            6: utcnow,
            7: utcnow,
            8: utcnow,
            9: utcnow,
        }, last_sync)

    def test_get_latest_source_success_archived_campaign(self):
        c = dash.models.Campaign.objects.get(id=1)
        for ag in c.adgroup_set.all():
            for ags in ag.adgroupsource_set.all():
                ags.last_successful_sync_dt = None
                ags.save()

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual({
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
            7: None,
        }, last_sync)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        c.archive(r)

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_latest_source_success_archived_ad_group(self):
        ag = dash.models.AdGroup.objects.get(id=1)
        for ags in ag.adgroupsource_set.all():
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual({
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
            7: None,
        }, last_sync)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        ag.archive(r)

        last_sync = sync.AccountSync(self.acc).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)


class CampaignLastSuccessfulChildSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.campaign = dash.models.Campaign.objects.get(id=1)

    def test_get_latest_success_by_child(self):
        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            9: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_latest_success_by_child_none(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: None,
            9: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_latest_success_by_child_deprecated(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            9: datetime.datetime(2014, 6, 10, 9, 58, 21),
        }, last_sync)

    def test_get_latest_success_by_child_sources_filtered(self):
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__campaign=self.campaign, source_id__in=[2, 7]):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: None,
            9: None,
        }, last_sync)

        last_sync = sync.CampaignSync(
            self.campaign,
            sources=dash.models.Source.objects.filter(id__in=[1, 3, 6])
        ).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_exclude_archived_ad_group(self):
        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            9: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

        ag = dash.models.AdGroup.objects.get(id=9)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        ag.archive(r)

        last_sync = sync.CampaignSync(self.campaign).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_success_by_child_demo_campaign(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        campaign = dash.models.Campaign.objects.get(id=6)
        last_sync = sync.CampaignSync(campaign).get_latest_success_by_child()
        self.assertEqual({
            8: utcnow,
        }, last_sync)


class CamapaignLastSuccessfulSourceSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.campaign = dash.models.Campaign.objects.get(id=1)

    def test_get_latest_source_success(self):
        last_sync = sync.CampaignSync(self.campaign).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
            7: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_source_success_maintenance(self):
        s = dash.models.Source.objects.get(id=6)
        self.assertTrue(s.maintenance)

        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_deprecated(self):
        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        s = dash.models.Source.objects.get(id=6)
        s.deprecated = True
        s.maintenance = False
        s.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_sources_filtered(self):
        last_sync = sync.CampaignSync(
            self.campaign,
            sources=dash.models.Source.objects.filter(id__in=[1, 2, 3])
        ).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_source_success_demo_campaign(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        campaign = dash.models.Campaign.objects.get(id=6)
        last_sync = sync.CampaignSync(campaign).get_latest_source_success()
        self.assertEqual({
            1: utcnow,
            2: utcnow,
            3: utcnow,
            4: utcnow,
            5: utcnow,
            6: utcnow,
            7: utcnow,
            8: utcnow,
            9: utcnow,
        }, last_sync)

    def test_get_latest_source_success_archived_ad_group(self):
        for ags in dash.models.AdGroupSource.objects.filter(ad_group_id=9):
            ags.last_successful_sync_dt = None
            ags.save()

        last_sync = sync.CampaignSync(self.campaign).get_latest_source_success()
        self.assertEqual(None, last_sync[2])

        ag = dash.models.AdGroup.objects.get(id=9)

        r = HttpRequest()
        r.user = zemauth.models.User.objects.create_user('test@example.com')
        ag.archive(r)

        last_sync = sync.CampaignSync(self.campaign).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[2])


class AdGroupLastSuccessfulChildSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group = dash.models.AdGroup.objects.get(id=1)

    def test_get_latest_success_by_child(self):
        last_sync = sync.AdGroupSync(self.ad_group).get_latest_success_by_child()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            18: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_success_by_child_none(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.save()

        last_sync = sync.AdGroupSync(self.ad_group).get_latest_success_by_child()
        self.assertEqual(None, last_sync[9])

    def test_get_latest_success_by_child_deprecated(self):
        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.AdGroupSync(self.ad_group).get_latest_success_by_child()
        self.assertTrue(9 not in last_sync)

    def test_get_latest_success_by_child_sources_filtered(self):
        last_sync = sync.AdGroupSync(
            self.ad_group,
            sources=dash.models.Source.objects.filter(id__in=[1, 2, 3])
        ).get_latest_success_by_child()
        ags_ids = dash.models.AdGroupSource.objects\
                                           .filter(ad_group=self.ad_group, source_id__in=[1, 2, 3])\
                                           .values_list('id', flat=True)
        self.assertItemsEqual(
            ags_ids,
            last_sync.keys()
        )


class AdGroupLastSuccessfulSourceSyncTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group = dash.models.AdGroup.objects.get(id=1)

    def test_get_latest_source_success(self):
        last_sync = sync.AdGroupSync(self.ad_group).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21),
            4: datetime.datetime(2014, 6, 10, 9, 58, 21),
            5: datetime.datetime(2014, 6, 10, 9, 58, 21),
            6: None,
            7: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    def test_get_latest_source_success_maintenance(self):
        s = dash.models.Source.objects.get(id=6)
        self.assertTrue(s.maintenance)

        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        last_sync = sync.AdGroupSync(self.ad_group).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_deprecated(self):
        ags = dash.models.AdGroupSource.objects.get(ad_group_id=1, source_id=6)
        ags.last_successful_sync_dt = datetime.datetime(2014, 6, 10, 9, 58, 21)
        ags.save()

        s = dash.models.Source.objects.get(id=6)
        s.maintenance = False
        s.deprecated = True
        s.save()

        last_sync = sync.AdGroupSync(self.ad_group).get_latest_source_success()
        self.assertEqual(datetime.datetime(2014, 6, 10, 9, 58, 21), last_sync[6])

    def test_get_latest_source_success_sources_filtered(self):
        last_sync = sync.AdGroupSync(
            self.ad_group,
            sources=dash.models.Source.objects.filter(id__in=[1, 2, 3])
        ).get_latest_source_success()
        self.assertEqual({
            1: datetime.datetime(2014, 6, 10, 9, 58, 21),
            2: datetime.datetime(2014, 6, 10, 9, 58, 21),
            3: datetime.datetime(2014, 6, 10, 9, 58, 21)
        }, last_sync)

    @mock.patch('actionlog.sync.datetime', test_helper.MockDateTime)
    def test_get_latest_source_success_demo_ad_group(self):
        utcnow = datetime.datetime.utcnow()
        sync.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dash.models.AdGroup.objects.get(id=8)

        last_sync = sync.AdGroupSync(ad_group).get_latest_source_success()
        self.assertEqual({
            1: utcnow,
            2: utcnow,
            3: utcnow,
            4: utcnow,
            5: utcnow,
            6: utcnow,
            7: utcnow,
            8: utcnow,
            9: utcnow,
        }, last_sync)


class ActionLogTriggerSyncTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def setUp(self):
        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_reports(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        dates = last_n_days(3)

        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=6)
        )
        ags_sync.trigger_reports_for_dates(dates)

        actions = actionlog.models.ActionLog.objects.filter(
            created_dt__isnull=False).order_by('-created_dt')
        actions = list(actions)

        self.assertEqual(len(actions) > 3, True)
        self.assertEqual(actions[0].created_dt.date() == actions[1].created_dt.date() == actions[2].created_dt.date(), True)
        self.assertEqual(actions[3].created_dt.date() < actions[2].created_dt.date(), True)

        for action in actions[:3]:
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertIn(
                action.action,
                (constants.Action.FETCH_REPORTS, )
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_content_ad_status(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)

        self.assertFalse(actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.GET_CONTENT_AD_STATUS).exists())

        ags_sync = sync.AdGroupSourceSync(ad_group_source)

        ags_sync.trigger_content_ad_status()

        action_logs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.GET_CONTENT_AD_STATUS)

        self.assertEqual(len(action_logs), 1)

        self.assertEqual(action_logs[0].state, constants.ActionState.WAITING)
        self.assertEqual(action_logs[0].action, constants.Action.GET_CONTENT_AD_STATUS)
        self.assertEqual(action_logs[0].action_type, constants.ActionType.AUTOMATIC)

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_content_ad_status_no_ads(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=6)

        self.assertFalse(actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.GET_CONTENT_AD_STATUS).exists())

        ags_sync = sync.AdGroupSourceSync(ad_group_source)

        ags_sync.trigger_content_ad_status()

        exists = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.GET_CONTENT_AD_STATUS).exists()

        self.assertFalse(exists)

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_status(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        self.assertEqual(
            len(actionlog.models.ActionLog.objects.filter(ad_group_source=6)),
            0
        )

        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=6)
        )
        ags_sync.trigger_status()

        self.assertEqual(
            len(actionlog.models.ActionLog.objects.filter(ad_group_source=6)),
            1
        )

        alog = actionlog.models.ActionLog.objects.filter(ad_group_source=6)[0]
        self.assertEqual(alog.state, constants.ActionState.WAITING)
        self.assertEqual(alog.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(alog.action_type, constants.ActionType.AUTOMATIC)

    def test_ad_group_source_get_dates_to_sync_reports(self):
        ad_group_source =dash.models.AdGroupSource.objects.get(pk=5)
        ags_sync = sync.AdGroupSourceSync(ad_group_source)

        dates = ags_sync.get_dates_to_sync_reports()
        dates = list(dates)

        self.assertEqual(dates[0], datetime.datetime.utcnow().date())
        self.assertEqual(dates[-1], ad_group_source.last_successful_sync_dt.date() - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS - 1))
        self.assertEqual(
            len(dates),
            (datetime.datetime.utcnow().date() - (
                ad_group_source.last_successful_sync_dt.date() - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS - 1)
            )).days + 1
        )


class ActionLogSyncGetComponentsTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def test_global_sync_get_components(self):
        global_sync = sync.GlobalSync()
        child_syncs = global_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 3)

    def test_account_sync_get_components(self):
        account = dash.models.Account.objects.get(pk=2)

        account_sync = sync.AccountSync(account)
        child_syncs = account_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 1)

    def test_campaign_sync_get_components(self):
        campaign = dash.models.Campaign.objects.get(pk=3)

        campaign_sync = sync.CampaignSync(campaign)
        child_syncs = campaign_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 2)
