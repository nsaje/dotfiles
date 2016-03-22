# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

import pytz
from django.db.models.signals import pre_save
from django.test import TestCase
from django.http.request import HttpRequest
from django.conf import settings

from dash import models, constants
from dash.constants import GATrackingType
from zemauth import models as zemauthmodels
from zemauth.models import User
from utils import exc


class AdGroupSettingsTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_settings_fields(self):
        meta_fields = [
            'id',
            'ad_group',
            'ad_group_id',
            'created_dt',
            'created_by',
            'created_by_id',
            'changes_text',
            'useractionlog',
            'system_user'
        ]

        all_fields = set(models.AdGroupSettings._settings_fields + meta_fields)
        model_fields = set(models.AdGroupSettings._meta.get_all_field_names())

        self.assertEqual(model_fields, all_fields)

    def test_get_settings_dict(self):
        settings_dict = {
            'archived': False,
            'state': 1,
            'cpc_cc': Decimal('1.00'),
            'daily_budget_cc': Decimal('50.0000'),
            'start_date': datetime.date(2014, 6, 4),
            'end_date': datetime.date(2014, 6, 5),
            'target_devices': ['mobile'],
            'tracking_code': u'',
            'target_regions': ['US'],
            'retargeting_ad_groups': [1, 2],
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'ad_group_name': 'AdGroup name',
            'enable_ga_tracking': True,
            'enable_adobe_tracking': False,
            'adobe_tracking_param': '',
            'autopilot_daily_budget': Decimal('0.0000'),
            'autopilot_state': 2,
            'ga_tracking_type': GATrackingType.EMAIL,
        }
        self.assertEqual(
            models.AdGroupSettings.objects.get(id=1).get_settings_dict(),
            settings_dict,
        )

    def test_get_tracking_ids(self):
        ad_group_settings = models.AdGroupSettings.objects.get(id=1)
        self.assertEqual(ad_group_settings.get_tracking_codes(), u'')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.tracking_code = '?param1=value1&param2=value2#hash?a=b&c=d'
        new_ad_group_settings.save(request)
        self.assertEqual(new_ad_group_settings.get_tracking_codes(), u'param1=value1&param2=value2#hash?a=b&c=d')

    def test_adgroup_settings_end_datetime(self):
        ad_group_settings = models.AdGroupSettings()
        self.assertEqual(ad_group_settings.get_utc_end_datetime(), None)

        ad_group_settings = models.AdGroupSettings(end_date=datetime.date(2015, 4, 29))
        self.assertEqual(ad_group_settings.get_utc_end_datetime().tzinfo, None)

        dt = datetime.datetime(2015, 4, 29, 1, tzinfo=pytz.timezone(settings.DEFAULT_TIME_ZONE)).\
            astimezone(pytz.timezone('UTC')).\
            replace(tzinfo=None)
        self.assertTrue(ad_group_settings.get_utc_end_datetime() > dt)

    def test_adgroup_settings_start_datetime(self):
        ad_group_settings = models.AdGroupSettings()
        self.assertEqual(ad_group_settings.get_utc_start_datetime(), None)

        ad_group_settings = models.AdGroupSettings(start_date=datetime.date(2015, 4, 29))
        self.assertEqual(ad_group_settings.get_utc_start_datetime().tzinfo, None)

        dt = datetime.datetime(2015, 4, 29, 1, tzinfo=pytz.timezone(settings.DEFAULT_TIME_ZONE)).\
            astimezone(pytz.timezone('UTC')).\
            replace(tzinfo=None)
        self.assertTrue(ad_group_settings.get_utc_start_datetime() < dt)

    def test_get_changes_text_unicode(self):
        old_settings = models.AdGroupSettings.objects.get(id=1)
        new_settings = models.AdGroupSettings.objects.get(id=1)
        new_settings.changes_text = None
        new_settings.ad_group_name = u'Ččšćžđ name'

        user = User.objects.get(pk=1)

        self.assertEqual(
            models.AdGroupSettings.get_changes_text(old_settings, new_settings, user),
            u'Ad group name set to "\u010c\u010d\u0161\u0107\u017e\u0111 name"')

    def test_get_changes_text(self):
        old_settings = models.AdGroupSettings(ad_group_id=1)
        new_settings = models.AdGroupSettings.objects.get(id=1)
        new_settings.changes_text = None

        user = User.objects.get(pk=1)

        self.assertEqual(
            models.AdGroupSettings.get_changes_text(old_settings, new_settings, user),
            'Daily budget set to "$50.00", '
            'Locations set to "United States", '
            'Description set to "Example description", '
            'End date set to "2014-06-05", '
            'Max CPC bid set to "$1.00", '
            'Device targeting set to "Mobile", '
            'Display URL set to "example.com", '
            'Brand name set to "Example", '
            'State set to "Enabled", '
            'Call to action set to "Call to action", '
            'Ad group name set to "AdGroup name", '
            'Start date set to "2014-06-04", '
            'Retargeting ad groups set to "test adgroup 1, test adgroup 2"'
        )

    def test_get_changes_text_no_permissions(self):
        user = User.objects.create()
        old_settings = models.AdGroupSettings(ad_group_id=1)
        new_settings = models.AdGroupSettings.objects.get(id=1)
        new_settings.changes_text = None

        user = User.objects.create(email="test.user@test.com")

        self.assertEqual(
            models.AdGroupSettings.get_changes_text(old_settings, new_settings, user),
            'Daily budget set to "$50.00", '
            'Locations set to "United States", '
            'End date set to "2014-06-05", '
            'Max CPC bid set to "$1.00", '
            'Device targeting set to "Mobile", '
            'State set to "Enabled", '
            'Ad group name set to "AdGroup name", '
            'Start date set to "2014-06-04"'
        )


class AdGroupRunningStatusTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_running_by_flight_time(self):

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.start_date = datetime.date.today() - datetime.timedelta(days=1)
        ad_group_settings.end_date = datetime.date.today() + datetime.timedelta(days=1)
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        self.assertEqual(
            models.AdGroup.get_running_status_by_flight_time(ad_group_settings),
            constants.AdGroupRunningStatus.ACTIVE
        )

    def test_running_by_flight_time_end_today(self):

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.start_date = datetime.date.today() - datetime.timedelta(days=1)
        ad_group_settings.end_date = datetime.date.today()
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        self.assertEqual(
            models.AdGroup.get_running_status_by_flight_time(ad_group_settings),
            constants.AdGroupRunningStatus.ACTIVE
        )

    def test_running_by_flight_time_no_end(self):

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.start_date = datetime.date.today() - datetime.timedelta(days=1)
        ad_group_settings.end_date = None
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        self.assertEqual(
            models.AdGroup.get_running_status_by_flight_time(ad_group_settings),
            constants.AdGroupRunningStatus.ACTIVE
        )

    def test_not_running_by_flight_time(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.start_date = datetime.date.today() - datetime.timedelta(days=2)
        ad_group_settings.end_date = datetime.date.today() - datetime.timedelta(days=1)
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        self.assertEqual(
            models.AdGroup.get_running_status_by_flight_time(ad_group_settings),
            constants.AdGroupRunningStatus.INACTIVE
        )

    def test_not_running_by_flight_time_settings_state(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.start_date = datetime.date.today() - datetime.timedelta(days=1)
        ad_group_settings.end_date = datetime.date.today() + datetime.timedelta(days=1)
        ad_group_settings.state = constants.AdGroupSettingsState.INACTIVE

        self.assertEqual(
            models.AdGroup.get_running_status_by_flight_time(ad_group_settings),
            constants.AdGroupRunningStatus.INACTIVE
        )

    def test_not_running_by_sources_state(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        ad_group_sources_settings = models.AdGroupSourceSettings.objects\
                                                                .filter(ad_group_source__source_id__in=[3])\
                                                                .group_current_settings()

        self.assertEqual(
            models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, ad_group_sources_settings),
            constants.AdGroupRunningStatus.INACTIVE,
            msg="All the sources are inactive, running status should be inactive"
        )

    def test_running_by_sources_state(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        ad_group_sources_settings = models.AdGroupSourceSettings.objects\
                                                                .filter(ad_group_source__source_id__in=[1, 2, 3])\
                                                                .group_current_settings()
        self.assertEqual(
            models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, ad_group_sources_settings),
            constants.AdGroupRunningStatus.ACTIVE,
            msg="Some sources are active, running status should be active")

    def test_no_running_by_sources_state_ag_settings_inactive(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.state = constants.AdGroupSettingsState.INACTIVE

        ad_group_sources_settings = models.AdGroupSourceSettings.objects\
                                                                .filter(ad_group_source__source_id__in=[1, 2, 3])\
                                                                .group_current_settings()
        self.assertEqual(
            models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, ad_group_sources_settings),
            constants.AdGroupRunningStatus.INACTIVE,
            msg="Ad group settings are inactive, ad group should not run")

    def test_not_running_by_sources_state_inactive(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE

        ad_group_sources_settings = models.AdGroupSourceSettings.objects\
                                                                .filter(ad_group_source__source_id__in=[1, 2, 3])\
                                                                .group_current_settings()
        for agss in ad_group_sources_settings.iterator():
            new_agss = agss.copy_settings()
            new_agss.state = constants.AdGroupSourceSettingsState.INACTIVE
            new_agss.save(None)

        self.assertEqual(
            models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, ad_group_sources_settings),
            constants.AdGroupRunningStatus.INACTIVE,
            msg="No sources are active, ad group doesn't run")


class CampaignSettingsTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_settings_fields(self):
        meta_fields = [
            'id',
            'campaign',
            'campaign_id',
            'created_dt',
            'created_by',
            'created_by_id',
            'changes_text',
            'useractionlog',
            'campaign_manager_id',
        ]

        all_fields = set(models.CampaignSettings._settings_fields + meta_fields)
        model_fields = set(models.CampaignSettings._meta.get_all_field_names())

        self.assertEqual(model_fields, all_fields)

    def test_get_settings_dict(self):
        settings_dict = {
            'archived': False,
            'iab_category': u'1',
            'name': u'Test campaign 1',
            'target_devices': [u'mobile'],
            'campaign_manager': User.objects.get(pk=1),
            'promotion_goal': 1,
            'target_regions': [u'CA', u'501'],
            'service_fee': Decimal('0.2000'),
            'campaign_goal': 2,
            'goal_quantity': Decimal('10.00'),
            'automatic_landing_mode': False,
            'landing_mode': False,
        }

        self.assertEqual(
            models.CampaignSettings.objects.get(id=1).get_settings_dict(),
            settings_dict,
        )

    def test_get_changes_text_unicode(self):
        old_settings = models.CampaignSettings.objects.get(id=1)
        new_settings = models.CampaignSettings.objects.get(id=1)
        new_settings.changes_text = None
        new_settings.name = u'Ččšćžđ name'

        user = User.objects.create_user('test@example.com')
        user.first_name = 'Tadej'
        user.last_name = u'Pavlič'
        new_settings.campaign_manager = user

        self.assertEqual(
            models.CampaignSettings.get_changes_text(old_settings, new_settings), u'Campaign Manager set to "Tadej Pavli\u010d", Name set to "\u010c\u010d\u0161\u0107\u017e\u0111 name"')

    def test_get_changes_text_nonunicode(self):
        old_settings = models.CampaignSettings.objects.get(id=1)
        new_settings = models.CampaignSettings.objects.get(id=1)
        new_settings.changes_text = None
        new_settings.name = u'name'

        user = User.objects.create_user('test@example.com')
        user.first_name = 'Tadej'
        user.last_name = u'Pavlic'
        new_settings.campaign_manager = user

        self.assertEqual(
            models.CampaignSettings.get_changes_text(old_settings, new_settings), u'Campaign Manager set to "Tadej Pavlic", Name set to "name"')


class AdGroupSourceTest(TestCase):

    def test_adgroup_source_save(self):
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        ad_group = models.AdGroup(campaign_id=1, modified_by_id=1)
        ad_group.save(request)

        source = models.Source.objects.create()

        ad_group_source = models.AdGroupSource(ad_group=ad_group, source=source)
        ad_group_source.save(request)

        self.assertTrue(models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).exists())

    def test_get_tracking_ids(self):
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        ad_group = models.AdGroup(campaign_id=1, modified_by_id=1)
        ad_group.save(request)

        source_type = models.SourceType.objects.create()
        source = models.Source.objects.create(source_type=source_type)

        ad_group_source = models.AdGroupSource(ad_group=ad_group, source=source)
        ad_group_source.save(request)

        self.assertEqual(ad_group_source.get_tracking_ids(), '_z1_adgid=%s&_z1_msid=' % (ad_group.id))

        source_type.type = constants.SourceType.ZEMANTA
        source_type.save()
        self.assertEqual(ad_group_source.get_tracking_ids(), '_z1_adgid=%s&_z1_msid={sourceDomain}' % ad_group.id)

        source_type.type = constants.SourceType.B1
        source_type.save()
        self.assertEqual(ad_group_source.get_tracking_ids(), '_z1_adgid=%s&_z1_msid={sourceDomain}' % ad_group.id)

        source_type.type = 'not' + constants.SourceType.ZEMANTA + 'and not ' + constants.SourceType.B1
        source_type.save()

        source.tracking_slug = 'not_b1_zemanta'
        source.save()

        self.assertEqual(
            ad_group_source.get_tracking_ids(),
            '_z1_adgid=%s&_z1_msid=%s' % (ad_group.id, source.tracking_slug)
        )


class ContentAdTest(TestCase):

    def test_url_with_tracking_codes(self):
        content_ad = models.ContentAd(url='http://test.com/path')
        self.assertEqual(content_ad.url_with_tracking_codes('a=b'), 'http://test.com/path?a=b')

        content_ad.url = 'http://test.com/path?c=d'
        self.assertEqual(content_ad.url_with_tracking_codes('a=b'), 'http://test.com/path?c=d&a=b')

        content_ad.url = 'http://test.com/path?c=d'
        self.assertEqual(content_ad.url_with_tracking_codes(''), 'http://test.com/path?c=d')

        content_ad.url = 'http://test.com/path?c=d#fragment'
        self.assertEqual(content_ad.url_with_tracking_codes('a=b'), 'http://test.com/path?c=d&a=b#fragment')

        content_ad.url = 'http://ad.doubleclick.net/ddm/clk/289560433;116564310;c?http://d.agkn.com/pixel/2389/?che=%25n&col=%25ebuy!,1922531,%25epid!,%25eaid!,%25erid!&l0=http://analytics.bluekai.com/site/15823?phint=event%3Dclick&phint=aid%3D%25eadv!&phint=pid%3D%25epid!&phint=cid%3D%25ebuy!&phint=crid%3D%25ecid!&done=http%3A%2F%2Fiq.intel.com%2Fcrazy-for-march-madness-data%2F%3Fdfaid%3D1%26crtvid%3D%25ecid!%26dclid%3D1-%25eadv!-%25ebuy!-%25epid!-%25eaid!-%25erid!%26sr_source%3Dlift_zemanta%26ver%3D167_t1_i1%26_z1_msid%3D{sourceDomain}%26_z1_adgid%3D537'
        self.assertEqual(content_ad.url_with_tracking_codes('a=b'), 'http://ad.doubleclick.net/ddm/clk/289560433;116564310;c?http://d.agkn.com/pixel/2389/?che=%25n&col=%25ebuy!,1922531,%25epid!,%25eaid!,%25erid!&l0=http://analytics.bluekai.com/site/15823?phint=event%3Dclick&phint=aid%3D%25eadv!&phint=pid%3D%25epid!&phint=cid%3D%25ebuy!&phint=crid%3D%25ecid!&done=http%3A%2F%2Fiq.intel.com%2Fcrazy-for-march-madness-data%2F%3Fdfaid%3D1%26crtvid%3D%25ecid!%26dclid%3D1-%25eadv!-%25ebuy!-%25epid!-%25eaid!-%25erid!%26sr_source%3Dlift_zemanta%26ver%3D167_t1_i1%26_z1_msid%3D{sourceDomain}%26_z1_adgid%3D537&a=b')


def created_by_patch(sender, instance, **kwargs):
    u = zemauthmodels.User.objects.get(id=1)
    if instance.pk is not None:
        return

    instance.created_by = u


class ArchiveRestoreTestCase(TestCase):

    fixtures = ['test_models.yaml']

    def setUp(self):
        pre_save.connect(created_by_patch, sender=models.AdGroupSettings)
        pre_save.connect(created_by_patch, sender=models.CampaignSettings)
        pre_save.connect(created_by_patch, sender=models.AccountSettings)

        self.request = HttpRequest()
        self.request.user = User.objects.create_user('test@example.com')

    def tearDown(self):
        pre_save.disconnect(created_by_patch, sender=models.AdGroupSettings)
        pre_save.disconnect(created_by_patch, sender=models.CampaignSettings)
        pre_save.disconnect(created_by_patch, sender=models.AccountSettings)

    def test_archive_ad_group(self):
        ag1 = models.AdGroup.objects.get(id=1)
        ag2 = models.AdGroup.objects.get(id=2)

        self.assertFalse(ag1.get_current_settings().archived)
        self.assertFalse(ag2.get_current_settings().archived)

        self.assertFalse(ag1.can_archive())
        self.assertTrue(ag2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            ag1.archive(self.request)

        ag2.archive(self.request)
        self.assertTrue(ag2.get_current_settings().archived)

    def test_archive_campaign(self):
        c1 = models.Campaign.objects.get(id=1)
        c2 = models.Campaign.objects.get(id=2)

        self.assertFalse(c1.get_current_settings().archived)
        self.assertFalse(c2.get_current_settings().archived)

        self.assertFalse(c1.can_archive())
        self.assertTrue(c2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            c1.archive(self.request)

        c2.archive(self.request)
        self.assertTrue(c2.get_current_settings().archived)

        ag = c2.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_archive_account(self):
        a1 = models.Account.objects.get(id=1)
        a2 = models.Account.objects.get(id=2)

        self.assertFalse(a1.get_current_settings().archived)
        self.assertFalse(a2.get_current_settings().archived)

        self.assertFalse(a1.can_archive())
        self.assertTrue(a2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            a1.archive(self.request)

        a2.archive(self.request)
        self.assertTrue(a2.get_current_settings().archived)

        c = a2.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_account(self):
        a = models.Account.objects.get(id=2)

        self.assertTrue(a.can_archive())
        a.archive(self.request)

        self.assertTrue(a.can_restore())
        a.restore(self.request)

        self.assertFalse(a.get_current_settings().archived)

        c = a.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_campaign(self):
        c = models.Campaign.objects.get(id=2)

        self.assertTrue(c.can_archive())
        c.archive(self.request)

        self.assertTrue(c.can_restore())
        c.restore(self.request)

        self.assertFalse(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_ad_group(self):
        ag = models.AdGroup.objects.get(id=2)

        self.assertTrue(ag.can_archive())
        ag.archive(self.request)

        self.assertTrue(ag.can_restore())
        ag.restore(self.request)

        self.assertFalse(ag.get_current_settings().archived)

    def test_restore_campaign_fail(self):
        a = models.Account.objects.get(id=2)

        a.archive(self.request)

        c = a.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)
        self.assertFalse(c.can_restore())

        with self.assertRaises(exc.ForbiddenError):
            c.restore(self.request)

        a.restore(self.request)
        self.assertTrue(c.get_current_settings().archived)
        self.assertTrue(c.can_restore())

        c.restore(self.request)
        self.assertFalse(c.get_current_settings().archived)

    def test_restore_ad_group_fail(self):
        c = models.Campaign.objects.get(id=2)

        c.archive(self.request)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)
        self.assertFalse(ag.can_restore())

        with self.assertRaises(exc.ForbiddenError):
            ag.restore(self.request)

        c.restore(self.request)
        self.assertTrue(ag.get_current_settings().archived)
        self.assertTrue(ag.can_restore())

        ag.restore(self.request)
        self.assertFalse(ag.get_current_settings().archived)


class AdGroupTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.AdGroup.objects.all().exclude_archived()

        self.assertEqual(len(qs), 7)


class CampaignTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.Campaign.objects.all().exclude_archived()

        self.assertEqual(len(qs), 4)

    def test_get_current_settings(self):
        campaign = models.Campaign.objects.get(pk=2)

        settings = campaign.get_current_settings()

        self.assertEqual(settings.name, 'test campaign 2')
        self.assertEqual(settings.iab_category, 'IAB24')
        self.assertEqual(settings.target_devices, ['mobile'])
        self.assertEqual(settings.target_regions, ['US'])

    def test_get_current_settings_no_existing_settings(self):
        campaign = models.Campaign.objects.get(pk=1)

        self.assertEqual(len(models.CampaignSettings.objects.filter(campaign_id=campaign.id)), 0)

        settings = campaign.get_current_settings()

        self.assertEqual(settings.name, '')
        self.assertEqual(settings.iab_category, 'IAB24')
        self.assertEqual(settings.target_devices, ['mobile', 'desktop'])
        self.assertEqual(settings.target_regions, ['US'])


class AccountTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.Account.objects.all().exclude_archived()

        self.assertEqual(len(qs), 3)
