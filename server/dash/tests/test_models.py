# -*- coding: utf-8 -*-
import datetime
import textwrap
from decimal import Decimal

import pytz
from mock import patch
from django.db.models.signals import pre_save
from django.test import TestCase, override_settings
from django.http.request import HttpRequest
from django.core.exceptions import ValidationError
from django.conf import settings
from django.forms.models import model_to_dict

from dash import models, constants
from dash.constants import GATrackingType
from zemauth import models as zemauthmodels
from zemauth.models import User
from utils import exc, test_helper


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
            'exclusion_retargeting_ad_groups': [3, 4],
            'notes': 'Some note',
            'bluekai_targeting': ['or', 3, 4],
            'interest_targeting': ['a', 'b'],
            'exclusion_interest_targeting': ['c', 'd'],
            'audience_targeting': [1, 2],
            'exclusion_audience_targeting': [3, 4],
            'redirect_pixel_urls': ['http://a.com/b.jpg', 'http://a.com/c.jpg'],
            'redirect_javascript': 'alert(\'a\')',
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'ad_group_name': 'AdGroup name',
            'autopilot_daily_budget': Decimal('0.0000'),
            'autopilot_state': 2,
            'landing_mode': False,
            'dayparting': {"monday": [1, 2, 5], "tuesday": [10, 12], "timezone": "CET"},
            'max_cpm': Decimal('1.6'),
            'b1_sources_group_enabled': True,
            'b1_sources_group_daily_budget': Decimal('5.0000'),
            'b1_sources_group_state': constants.AdGroupSourceSettingsState.ACTIVE,
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [],
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

        self.maxDiff = None
        self.assertHTMLEqual(
            models.AdGroupSettings.get_changes_text(old_settings, new_settings, user),
            'Daily spend cap set to "$50.00", '
            'Whitelist publisher groups set to "pg 1", '
            'Brand name set to "Example", '
            'Daily budget for all RTB sources set to "$5.00", '
            'Max CPC bid set to "$1.000", '
            'Interest targeting set to "A, B", '
            'Exclusion interest targeting set to "C, D", '
            'State set to "Enabled", '
            'Pixel retargeting tags set to "http://a.com/b.jpg, http://a.com/c.jpg", '
            'Start date set to "2014-06-04", '
            'State of all RTB sources set to "Enabled", '
            'Description set to "Example description", '
            'End date set to "2014-06-05", '
            'Custom audience targeting set to "test audience 1, test audience 2", '
            'Exclusion ad groups set to "test adgroup 3, test adgroup 4 on budget autopilot", '
            'Dayparting set to "Timezone: CET; Tuesday: 10, 12; Monday: 1, 2, 5", '
            'Exclusion custom audience targeting set to "test audience 3, test audience 4", '
            'Max CPM set to "$1.60", '
            'Retargeting ad groups set to "test adgroup 1, test adgroup 2", '
            'Locations set to "United States", '
            'Call to action set to "Call to action", '
            'Device targeting set to "Mobile", '
            'Notes set to "Some note", '
            'Display URL set to "example.com", '
            'Pixel retargeting JavaScript set to "alert(\'a\')", '
            'Group all RTB sources set to "True", '
            'Ad group name set to "AdGroup name", BlueKai targeting set to "["or", 3, 4]"'
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
            'campaign_manager_id',
            'system_user',
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
            'campaign_goal': 2,
            'goal_quantity': Decimal('10.00'),
            'automatic_campaign_stop': True,
            'landing_mode': False,
            'enable_ga_tracking': True,
            'ga_property_id': u'',
            'ga_tracking_type': 1,
            'enable_adobe_tracking': False,
            'adobe_tracking_param': u'',
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

        account = models.Account(name='test')
        account.save(request)

        campaign = models.Campaign(account=account)
        campaign.save(request)

        ad_group = models.AdGroup(campaign=campaign, modified_by_id=1)
        ad_group.save(request)

        source = models.Source.objects.create()

        ad_group_source = models.AdGroupSource(ad_group=ad_group, source=source)
        ad_group_source.save(request)

        self.assertTrue(models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).exists())

    def test_get_tracking_ids(self):
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        account = models.Account(name='test')
        account.save(request)

        campaign = models.Campaign(account=account)
        campaign.save(request)

        ad_group = models.AdGroup(campaign=campaign, modified_by_id=1)
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


@override_settings(
    IMAGE_THUMBNAIL_URL='http://test.com',
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

    def test_get_image_url(self):
        content_ad = models.ContentAd(image_id="foo", image_width=100, image_height=200)
        image_url = content_ad.get_image_url(500, 600)
        self.assertEqual(image_url, 'http://test.com/foo.jpg?w=500&h=600&fit=crop&crop=center&fm=jpg')

        image_url = content_ad.get_image_url()
        self.assertEqual(image_url, 'http://test.com/foo.jpg?w=100&h=200&fit=crop&crop=center&fm=jpg')

        content_ad = models.ContentAd(image_id=None, image_width=100, image_height=200)
        image_url = content_ad.get_image_url()
        self.assertEqual(image_url, None)

    def test_original_image_url(self):
        content_ad = models.ContentAd(image_id="foo", image_width=100, image_height=200)
        image_url = content_ad.get_original_image_url()
        self.assertEqual(image_url, 'http://test.com/foo.jpg')

        image_url = content_ad.get_original_image_url()
        self.assertEqual(image_url, 'http://test.com/foo.jpg')

        content_ad = models.ContentAd(image_id=None, image_width=100, image_height=200)
        image_url = content_ad.get_original_image_url()
        self.assertEqual(image_url, None)


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
        c3 = models.Campaign.objects.get(id=3)

        credit = models.CreditLineItem.objects.create(
            amount=10,
            account=c3.account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            status=1,
        )
        models.BudgetLineItem.objects.create(
            amount=credit.amount,
            start_date=credit.start_date,
            end_date=credit.end_date,
            credit=credit,
            campaign=c3,
        )

        self.assertFalse(c1.get_current_settings().archived)
        self.assertFalse(c2.get_current_settings().archived)
        self.assertFalse(c3.get_current_settings().archived)

        self.assertFalse(c1.can_archive())
        self.assertTrue(c2.can_archive())
        self.assertFalse(c3.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            c1.archive(self.request)

        with self.assertRaises(exc.ForbiddenError):
            c3.archive(self.request)

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

    def test_cannot_archive_ad_group_dates(self):
        ag = models.AdGroup.objects.get(id=2)

        cs = ag.get_current_settings()
        self.assertFalse(cs.archived)
        self.assertTrue(ag.can_archive())

        with test_helper.disable_auto_now_add(models.AdGroupSettings, 'created_dt'):
            # enable it before
            cs = cs.copy_settings()
            cs.state = constants.AdGroupSettingsState.ACTIVE
            cs.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL + 1)
            cs.save(self.request)

            cs = cs.copy_settings()
            cs.state = constants.AdGroupSettingsState.INACTIVE
            cs.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL)
            cs.save(self.request)

        self.assertFalse(ag.can_archive())

    def test_can_archive_ad_group_dates(self):
        ag = models.AdGroup.objects.get(id=2)

        cs = ag.get_current_settings()
        self.assertFalse(cs.archived)
        self.assertTrue(ag.can_archive())

        with test_helper.disable_auto_now_add(models.AdGroupSettings, 'created_dt'):
            # enable it before
            cs = cs.copy_settings()
            cs.state = constants.AdGroupSettingsState.ACTIVE
            cs.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL + 2)
            cs.save(self.request)

            # then pause
            cs = cs.copy_settings()
            cs.state = constants.AdGroupSettingsState.INACTIVE
            cs.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL + 1)
            cs.save(self.request)

        self.assertTrue(ag.can_archive())

    def test_can_archive_ad_group_dates_if_never_enabled(self):
        ag = models.AdGroup.objects.get(id=2)

        cs = ag.get_current_settings()
        self.assertFalse(cs.archived)
        self.assertTrue(ag.can_archive())
        self.assertEqual([x for x in ag.settings.all() if x.state == constants.AdGroupSettingsState.ACTIVE], [])

        with test_helper.disable_auto_now_add(models.AdGroupSettings, 'created_dt'):
            cs = cs.copy_settings()
            cs.state = constants.AdGroupSettingsState.INACTIVE
            cs.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL - 1)
            cs.save(self.request)

        self.assertTrue(ag.can_archive())


class AdGroupTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_agency.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=3)

    def test_filter_by_agency_manager(self):
        qs = models.AdGroup.objects.all().filter_by_user(self.user)
        oldcount = qs.count()
        self.assertGreater(oldcount, 0)

        agency = models.Agency.objects.get(pk=1)
        agency.users.add(self.user)
        qs = models.AdGroup.objects.all().filter_by_user(self.user)
        self.assertEqual(oldcount+1, qs.count())

    def test_filter_by_agencies(self):
        agencies = models.Agency.objects.filter(pk=1)

        qs = models.AdGroup.objects.all().filter_by_agencies(agencies)
        self.assertEqual(1, qs.count())

        agency = models.Agency.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)
        acc2.agency = agency
        acc2.save(test_helper.fake_request(self.user))

        qs = models.AdGroup.objects.all().filter_by_agencies(agencies)
        self.assertEqual(3, qs.count())

    def test_filter_by_account_type(self):
        all_adgroups = models.AdGroup.objects.all()
        qs = all_adgroups.filter_by_account_types([constants.AccountType.UNKNOWN])
        self.assertEqual(
            models.AdGroup.objects.all().filter(
                campaign__account__id=3
            ).count(),
            qs.count())

        qs = all_adgroups.filter_by_account_types([constants.AccountType.ACTIVATED])
        self.assertEqual(
            models.AdGroup.objects.all().filter(
                campaign__account__id=1
            ).count(),
            qs.count())

    def test_queryset_exclude_archived(self):
        qs = models.AdGroup.objects.all().exclude_archived()
        self.assertEqual(len(qs), 8)


class CampaignTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_agency.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=3)

    def test_filter_by_agency_manager(self):
        qs = models.Campaign.objects.all().filter_by_user(self.user)
        oldcount = qs.count()
        self.assertGreater(oldcount, 0)

        agency = models.Agency.objects.get(pk=1)
        agency.users.add(self.user)
        qs = models.Campaign.objects.all().filter_by_user(self.user)
        self.assertEqual(oldcount + 1, qs.count())

    def test_queryset_exclude_archived(self):
        qs = models.Campaign.objects.all().exclude_archived()
        self.assertEqual(len(qs), 5)

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
        self.assertEqual(settings.target_devices, ['tablet', 'mobile', 'desktop'])
        self.assertEqual(settings.target_regions, ['US'])

    def test_filter_by_agencies(self):
        agencies = models.Agency.objects.filter(pk=1)

        qs = models.Campaign.objects.all().filter_by_agencies(agencies)
        self.assertEqual(1, qs.count())

        agency = models.Agency.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)
        acc2.agency = agency
        acc2.save(test_helper.fake_request(self.user))

        qs = models.Campaign.objects.all().filter_by_agencies(agencies)
        self.assertEqual(2, qs.count())

    def test_filter_by_account_type(self):
        all_campaigns = models.Campaign.objects.all()
        qs = all_campaigns.filter_by_account_types([constants.AccountType.UNKNOWN])
        self.assertEqual(
            models.Campaign.objects.all().filter(
                account__id=3
            ).count(),
            qs.count())

        qs = all_campaigns.filter_by_account_types([constants.AccountType.ACTIVATED])
        self.assertEqual(
            models.Campaign.objects.all().filter(
                account__id=1
            ).count(),
            qs.count())


class AccountTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_agency.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=3)

    def test_filter_by_agency_manager(self):
        qs = models.Account.objects.all().filter_by_user(self.user)
        oldcount = qs.count()
        self.assertGreater(oldcount, 0)

        agency = models.Agency.objects.get(pk=1)
        agency.users.add(self.user)

        self.assertEqual(oldcount + 1, qs.count())

    def test_queryset_exclude_archived(self):
        qs = models.Account.objects.all().exclude_archived()
        self.assertEqual(len(qs), 4)

    def test_filter_by_agencies(self):
        agencies = models.Agency.objects.filter(pk=1)

        qs = models.Account.objects.all().filter_by_agencies(agencies)
        self.assertEqual(1, qs.count())

        agency = models.Agency.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)
        acc2.agency = agency
        acc2.save(test_helper.fake_request(self.user))

        qs = models.Account.objects.all().filter_by_agencies(agencies)
        self.assertEqual(2, qs.count())

    def test_filter_by_account_type(self):
        all_accounts = models.Account.objects.all()
        qs = all_accounts.filter_by_account_types([constants.AccountType.UNKNOWN])
        self.assertEqual(
            1,
            qs.count())

        qs = all_accounts.filter_by_account_types([constants.AccountType.ACTIVATED])
        self.assertEqual(
            1,
            qs.count())

        qs = all_accounts.filter_by_account_types([
            constants.AccountType.UNKNOWN,
            constants.AccountType.ACTIVATED,
        ])
        self.assertEqual(2, qs.count())


class CreditLineItemTestCase(TestCase):
    fixtures = ['test_api', 'test_agency']

    def test_create_acc_credit(self):
        acc = models.Account.objects.get(pk=1)
        user = User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)

        credit = models.CreditLineItem(
            account=acc,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )
        credit.save()
        self.assertGreater(models.CreditLineItem.objects.filter(pk=credit.id).count(), 0)

    def test_create_ag_credit(self):
        user = User.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)

        credit = models.CreditLineItem(
            agency=agency,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )
        credit.save()
        self.assertGreater(models.CreditLineItem.objects.filter(pk=credit.id).count(), 0)

    def test_create_credit_without_acc_and_ag(self):
        user = User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)

        credit = models.CreditLineItem(
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        with self.assertRaises(ValidationError):
            credit.save()

    def test_create_credit_with_acc_and_ag(self):
        acc = models.Account.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)

        credit = models.CreditLineItem(
            account=acc,
            agency=agency,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        with self.assertRaises(ValidationError):
            credit.save()


class HistoryTest(TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.u = User.objects.get(pk=1)
        self.acc = models.Account.objects.get(pk=1)
        self.su = constants.SystemUserType.AUTOPILOT

    def _latest_ad_group_history(self, ad_group=None):
        return models.History.objects.all().filter(
            ad_group=ad_group,
            level=constants.HistoryLevel.AD_GROUP
        ).order_by('-created_dt').first()

    def _latest_campaign_history(self, campaign=None):
        return models.History.objects.all().filter(
            campaign=campaign,
            level=constants.HistoryLevel.CAMPAIGN
        ).order_by('-created_dt').first()

    def _latest_account_history(self, account=None):
        return models.History.objects.all().filter(
            account=account,
            level=constants.HistoryLevel.ACCOUNT
        ).order_by('-created_dt').first()

    def test_save(self):
        models.History.objects.create(
            created_by=self.u,
            account=self.acc,
            level=constants.HistoryLevel.ACCOUNT,
        )
        self.assertEqual(1, models.History.objects.all().count())

    def test_save_system(self):
        models.History.objects.create(
            system_user=self.su,
            account=self.acc,
            level=constants.HistoryLevel.ACCOUNT,
        )
        self.assertEqual(1, models.History.objects.all().count())

    def test_save_no_creds(self):
        models.History.objects.create(
            account=self.acc,
            level=constants.HistoryLevel.ACCOUNT,
        )
        self.assertEqual(1, models.History.objects.all().count())

    def test_save_no_changes(self):
        adg = models.AdGroup.objects.get(pk=1)
        camp = models.Campaign.objects.get(pk=1)
        self.assertIsNone(
            adg.write_history(
                '',
                changes={},
            )
        )

        self.assertIsNone(
            camp.write_history(
                '',
                changes=None,
            )
        )

        self.assertIsNone(
            self.acc.write_history(
                '',
                changes={},
            )
        )

        self.assertEquals(0, models.History.objects.all().count())
        self.assertEquals(0, models.History.objects.all().count())
        self.assertEquals(0, models.History.objects.all().count())

    def test_save_fail(self):
        entry = models.History.objects.create(
            created_by=self.u,
            account=self.acc,
            level=constants.HistoryLevel.ACCOUNT,
        )
        with self.assertRaises(AssertionError):
            entry.delete()

        with self.assertRaises(AssertionError):
            models.History.objects.all().delete()

    def test_update_fail(self):
        models.History.objects.create(
            created_by=self.u,
            account=self.acc,
            level=constants.HistoryLevel.ACCOUNT,
        )
        with self.assertRaises(AssertionError):
            models.History.objects.update(changes_text='Something different')

    def test_create_ad_group_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        adgss = models.AdGroupSettings(
            ad_group=ad_group,
            cpc_cc=4.999,
        )
        adgss.save(None)

        hist = ad_group.write_history(
            '',
            changes=model_to_dict(adgss))

        self.assertEqual(ad_group, hist.ad_group)
        self.assertEqual(4.999, hist.changes['cpc_cc'])

        adgss = adgss.copy_settings()
        adgss.cpc_cc = 5.103
        adgss.save(None)

        adg_hist = self._latest_ad_group_history(ad_group=ad_group)
        self.maxDiff = None
        self.assertEqual(1, adg_hist.ad_group.id)
        self.assertDictEqual(
            {
                'cpc_cc': 5.103,
            }, adg_hist.changes
        )
        self.assertEqual(
            'Max CPC bid set from "$4.999" to "$5.103"',
            adg_hist.changes_text
        )

        hist = ad_group.write_history(
            '',
            changes={'cpc_cc': 5.101})

        self.assertEqual(ad_group, hist.ad_group)
        self.assertEqual({'cpc_cc': 5.101}, hist.changes)

    def test_create_ad_group_source_history(self):
        ad_group = models.AdGroup.objects.get(pk=2)
        source = models.Source.objects.get(pk=1)
        adgs = models.AdGroupSource.objects.filter(ad_group=ad_group, source=source).first()
        adgss = models.AdGroupSourceSettings(
            ad_group_source=adgs,
            daily_budget_cc=10000,
        )
        adgss.save(None)

        adgss = adgss.copy_settings()
        adgss.daily_budget_cc = 50000
        adgss.save(None)

        adgs_hist = self._latest_ad_group_history(ad_group=ad_group)
        self.assertDictEqual(
            {
                'daily_budget_cc': 50000,
            },
            adgs_hist.changes)
        self.assertEqual(
            textwrap.dedent("""
            Source: AdsNative. Daily Spend Cap set from "$10,000.00" to "$50,000.00"
            """).replace('\n', ''), adgs_hist.changes_text)

    def test_create_campaign_history(self):
        campaign = models.Campaign.objects.get(pk=1)
        adgss = models.CampaignSettings(
            campaign=campaign,
            name='Awesome',
        )
        adgss.save(None)

        hist = campaign.write_history(
            '',
            changes=model_to_dict(adgss),
        )

        self.assertEqual(campaign, hist.campaign)
        self.assertEqual('Awesome', hist.changes['name'])

        adgss = adgss.copy_settings()
        adgss.name = 'Awesomer'
        adgss.save(None)

        camp_hist = self._latest_campaign_history(campaign=campaign)
        self.assertDictEqual(
            {
                'name': 'Awesomer'
            },
            camp_hist.changes
        )
        self.assertEqual('Name set from "Awesome" to "Awesomer"', camp_hist.changes_text)

        hist = campaign.write_history(
            '',
            changes={'name': 'Awesomer'})

        self.assertEqual(campaign, hist.campaign)
        self.assertEqual({'name': 'Awesomer'}, hist.changes)

    def test_create_account_history(self):
        r = test_helper.fake_request(User.objects.get(pk=1))

        account = models.Account.objects.get(pk=1)
        adgss = models.AccountSettings(
            account=account,
            archived=False,
        )
        adgss.save(r)

        hist = account.write_history(
            "",
            changes=adgss.get_settings_dict(),
            )

        self.assertEqual(account, hist.account)
        self.assertFalse(hist.changes['archived'])

        hist = account.write_history(
            '',
            changes={'archived': True},
        )

        self.assertEqual(account, hist.account)
        self.assertEqual({'archived': True}, hist.changes)

        adgss = adgss.copy_settings()
        adgss.name = 'Wacky account'
        adgss.save(r)

        acc_hist = self._latest_account_history(account=account)
        self.assertDictEqual(
            {
                'name': 'Wacky account'
            },
            acc_hist.changes)
        self.assertEqual(
            'Name set to "Wacky account"',
            acc_hist.changes_text
        )

    @patch('dash.models.BudgetLineItem.state')
    def test_create_budget_history(self, mock_state):
        mock_state.return_value = constants.BudgetLineItemState.PENDING
        campaign = models.Campaign.objects.get(pk=1)
        hist = campaign.write_history(
            "",
            changes={'amount': 200},
        )

        self.assertEqual(campaign, hist.campaign)
        self.assertEqual({'amount': 200}, hist.changes)

    def test_create_credit_history(self):
        r = test_helper.fake_request(User.objects.get(pk=1))

        account = models.Account.objects.get(pk=1)
        start_date = datetime.date(2014, 6, 4)
        end_date = datetime.date(2014, 6, 5)
        campaign = models.Campaign.objects.get(pk=1)
        credit = models.CreditLineItem(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=10000,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=r.user,
        )
        credit.save()

        credit.amount = 20000
        credit.save()

        hist = account.write_history(
            '',
            changes={'amount': 20000},
        )

        self.assertEqual(account, hist.account)
        self.assertDictEqual({'amount': 20000}, hist.changes)

    def test_create_new_ad_group_history(self):
        campaign = models.Campaign.objects.get(pk=1)

        req = test_helper.fake_request(self.u)
        ad_group = models.AdGroup(
            name='Test group',
            campaign=campaign,
        )
        ad_group.save(req)
        new_settings = models.AdGroupSettings(
            ad_group=ad_group,
            cpc_cc=100
        )
        new_settings.save(req)

        history = models.History.objects.all().first()
        self.assertEqual(textwrap.dedent('''
            Created settings
            . State set to "Paused"
            , Max CPC bid set to "$100.000"
            , Device targeting set to ""
            , Locations set to "worldwide"
            , Autopilot set to "Disabled"
            , Autopilot\'s Daily Spend Cap set to "$0.00"
            , Landing Mode set to "False"
            ''').replace('\n', ''), history.changes_text)

    def test_create_new_campaign_history(self):
        account = models.Account.objects.get(pk=1)

        req = test_helper.fake_request(self.u)
        campaign = models.Campaign(
            name='Test campaign',
            account=account,
        )
        campaign.save(req)
        new_settings = campaign.get_current_settings()
        new_settings.name = 'Tested campaign'
        new_settings.save(req)

        history = models.History.objects.all().first()
        self.assertEqual(textwrap.dedent('''
            Created settings
            . Name set to "Tested campaign"
            , Device targeting set to "Tablet, Mobile, Desktop"
            , Locations set to "United States"
            ''').replace('\n', ''), history.changes_text)

    def test_create_new_account_history(self):
        req = test_helper.fake_request(self.u)
        account = models.Account(
            name='Test account',
        )
        account.save(req)
        new_settings = models.AccountSettings(
            name='Tested account',
            account=account,
        )
        new_settings.save(req)

        history = models.History.objects.all().first()
        self.assertEqual('Created settings', history.changes_text)

    def test_create_new_bcm_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()
        credit = models.CreditLineItem.objects.create(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.u,
        )

        history = models.History.objects.all().first()
        self.assertEqual(textwrap.dedent(
            '''
            Created credit
            . Credit: #{cid}. Status set to "Signed"
            , Comment set to ""
            , End Date set to "{ed}"
            , Flat Fee Start Date set to ""
            , Flat Fee (cc) set to "$0.00"
            , Start Date set to "{sd}"
            , Flat Fee End Date set to ""
            , Amount set to "$100.00"
            , License Fee set to "20.00%"
            '''.format(cid=credit.id,
                       sd=start_date.isoformat(),
                       ed=end_date.isoformat()))
            .replace('\n', ''), history.changes_text)

        budget = models.BudgetLineItem.objects.create(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.u,
        )

        history = models.History.objects.all().last()
        self.assertEqual(textwrap.dedent(
            '''
            Created budget
            . Budget: #{budid}. Comment set to ""
            , End Date set to "{ed}"
            , Start Date set to "{sd}"
            , Amount set to "$100.00"
            , Released amount set to "$0.00"
            , Margin set to "0.00%"
            '''.format(budid=budget.id,
                       sd=start_date.isoformat(),
                       ed=end_date.isoformat())
        ).replace('\n', ''), history.changes_text)

    def test_create_account(self):
        req = test_helper.fake_request(self.u)
        a = models.Account(
            name='test',
        )
        a.save(req)

        acs = a.get_current_settings()
        acs.save(req)

        hist = models.History.objects.all().order_by('-created_dt').first()
        self.assertEqual('Created settings', hist.changes_text)

    def test_create_campaign(self):
        req = test_helper.fake_request(self.u)
        c = models.Campaign(
            name='test',
            account=models.Account.objects.all().get(pk=1),
        )
        c.save(req)

        cs = c.get_current_settings()
        cs.save(req)

        hist = models.History.objects.all().order_by('-created_dt').first()
        self.assertEqual(textwrap.dedent('''
            Created settings
            . Device targeting set to "Tablet, Mobile, Desktop"
            , Locations set to "United States"
            ''').replace('\n', ''), hist.changes_text)

    def test_create_ad_group(self):
        req = test_helper.fake_request(self.u)
        a = models.AdGroup(
            name='test',
            campaign=models.Campaign.objects.all().get(pk=1),
        )
        a.save(req)

        adgs = a.get_current_settings()
        adgs.save(req)

        hist = models.History.objects.all().order_by('-created_dt').first()
        self.assertEqual(textwrap.dedent('''
            Created settings. State set to "Paused"
            , Start date set to "{}"
            , Daily spend cap set to "$10.00"
            , Device targeting set to "Tablet, Mobile, Desktop"
            , Locations set to "United States"
            , Autopilot set to "Disabled"
            , Autopilot\'s Daily Spend Cap set to "$0.00"
            , Landing Mode set to "False"
            ''').format(datetime.date.today().isoformat()).replace('\n', ''), hist.changes_text)

    def test_create_ad_group_source(self):
        s = models.Source.objects.create(
            name='b1'
        )
        ad_group = models.AdGroup.objects.get(pk=1)
        new_adgs = models.AdGroupSource(
            source=s,
            ad_group=ad_group
        )
        new_adgs.save()

        hist = models.History.objects.all().order_by('-created_dt').first()
        self.assertEqual('Created settings. Source: b1.', hist.changes_text)


@override_settings(CONVERSION_PIXEL_PREFIX='test_prefix')
class ConversionPixelTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def test_save(self):
        pixel = models.ConversionPixel.objects.create(account_id=1, name='Pixel name', id=4)
        self.assertEqual(pixel.slug, '4')
        pixel = models.ConversionPixel.objects.create(account_id=1, name='Pixel name', id=5, slug='testslug')
        self.assertEqual(pixel.slug, 'testslug')

    def test_get_url(self):
        self.assertEqual(len(models.ConversionPixel.objects.all()), 3)
        pixel = models.ConversionPixel.objects.create(account_id=1, name='Pixel name', id=4)

        self.assertEqual(pixel.get_url(), 'test_prefix1/4/')

        pixel = models.ConversionPixel.objects.create(account_id=1, name='Pixel name', slug='test_slug', id=5)

        self.assertEqual(pixel.get_url(), 'test_prefix1/test_slug/')


class SourceTypeTestCase(TestCase):

    def test_yahoo_desktop_min_cpc(self):
        source_type = models.SourceType(type=constants.SourceType.YAHOO, min_cpc=Decimal('0.05'))
        settings = models.AdGroupSettings(ad_group_id=1)
        settings_desktop = models.AdGroupSettings(ad_group_id=1, target_devices=[constants.AdTargetDevice.DESKTOP])
        self.assertEqual(source_type.get_min_cpc(settings), Decimal('0.05'))
        self.assertEqual(source_type.get_min_cpc(settings_desktop), Decimal('0.25'))


class PublisherGroupTest(TestCase):
    fixtures = ['test_publishers.yaml', 'test_models.yaml']

    def test_can_delete(self):
        pg = models.PublisherGroup.objects.get(pk=1)
        ags = models.AdGroup.objects.get(pk=1).get_current_settings()

        ags = ags.copy_settings()
        ags.whitelist_publisher_groups = [pg.id]
        ags.blacklist_publisher_groups = []
        ags.save(None)
        self.assertFalse(pg.can_delete())

        ags = ags.copy_settings()
        ags.whitelist_publisher_groups = []
        ags.blacklist_publisher_groups = []
        ags.save(None)
        self.assertTrue(pg.can_delete())
