import datetime
import pytz

from django.test import TestCase
from django.conf import settings
from django.http.request import HttpRequest

import actionlog.sync
from dash.views import helpers
from dash import models

from utils import exc
from zemauth.models import User


class ViewHelpersTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_get_ad_group_sources_last_sync_messages(self):
        ad_group_sources = models.AdGroupSource.objects.filter(pk__in=[1, 2, 3])

        last_successful_ags_sync_times = {}
        for ags in ad_group_sources:
            last_successful_ags_sync_times.update(
                actionlog.sync.AdGroupSourceSync(ags).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(ad_group_sources, last_successful_ags_sync_times)
        self.assertEqual(len(last_sync_messages), 3)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for ags in ad_group_sources:
            last_successful_source_sync_times.update(
                actionlog.sync.AdGroupSourceSync(ags).get_latest_source_success()
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 3)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

    def test_get_ad_group_last_sync_messages(self):
        ad_groups = models.AdGroup.objects.filter(pk__in=[1, 2])

        last_successful_ad_group_sync_times = {}
        for ag in ad_groups:
            last_successful_ad_group_sync_times.update(
                actionlog.sync.AdGroupSync(ag).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(ad_groups, last_successful_ad_group_sync_times)
        self.assertEqual(len(last_sync_messages), 2)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for ag in ad_groups:
            last_successful_source_sync_times.update(
                actionlog.sync.AdGroupSync(ag).get_latest_source_success()
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 7)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[4], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[5], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[6], ([], True))
        self.assertEquals(last_source_sync_messages[7], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_ad_groups = models.AdGroup.objects.filter(pk__in=[5])
        last_successful_archived_sync_times = {}
        for ad_group in archived_ad_groups:
            last_successful_archived_sync_times.update(
                actionlog.sync.AdGroupSync(ad_group).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(archived_ad_groups, last_successful_archived_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[5], ([], True))

    def test_get_campaign_last_sync_messages(self):
        campaigns = models.Campaign.objects.filter(pk__in=[1, 2])

        last_successful_campaign_sync_times = {}
        for campaign in campaigns:
            last_successful_campaign_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(campaigns, last_successful_campaign_sync_times)
        self.assertEqual(len(last_sync_messages), 2)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for campaign in campaigns:
            last_successful_source_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_source_success()
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 7)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[4], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[5], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[6], ([], True))
        self.assertEquals(last_source_sync_messages[7], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_campaigns = models.Campaign.objects.filter(pk__in=[4])
        last_successful_archived_sync_times = {}
        for campaign in archived_campaigns:
            last_successful_archived_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(archived_campaigns, last_successful_archived_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[4], ([], True))

    def test_get_account_last_sync_messages(self):
        accounts = models.Account.objects.filter(pk__in=[1])

        last_successful_account_sync_times = {}
        for account in accounts:
            last_successful_account_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(accounts, last_successful_account_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for account in accounts:
            last_successful_source_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_source_success()
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 7)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[4], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[5], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[6], ([], True))
        self.assertEquals(last_source_sync_messages[7], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_accounts = models.Account.objects.filter(pk__in=[3])
        last_successful_archived_sync_times = {}
        for account in archived_accounts:
            last_successful_archived_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_success_by_child()
            )

        last_sync_messages = helpers.get_last_sync_messages(archived_accounts, last_successful_archived_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[3], ([], True))

    def test_get_ad_group_sources_data_status(self):
        ad_group_source1 = models.AdGroupSource.objects.get(pk=1)
        ad_group_source2 = models.AdGroupSource.objects.get(pk=2)
        ad_group_source3 = models.AdGroupSource.objects.get(pk=3)
        ad_group_sources = [ad_group_source1, ad_group_source2, ad_group_source3]

        ad_group_settings = models.AdGroup.objects.get(id=1).get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)
        ad_group_sources_states = helpers.get_ad_group_sources_states(ad_group_sources)

        last_successful_ags_sync_times = {}
        for ags in ad_group_sources:
            last_successful_ags_sync_times.update(
                actionlog.sync.AdGroupSourceSync(ags).get_latest_success_by_child()
            )

        data_status = helpers.get_data_status(
            ad_group_sources,
            helpers.get_last_sync_messages(ad_group_sources, last_successful_ags_sync_times),
            helpers.get_ad_group_sources_state_messages(ad_group_sources,
                                                        ad_group_settings,
                                                        ad_group_sources_settings,
                                                        ad_group_sources_states)
        )

        self.assertEqual(data_status[ad_group_source1.source_id]['ok'], False)

        self.assertEqual(
            data_status[ad_group_source1.source_id]['message'],
            '<b>Status</b> for this Media Source differs from Status in the Media Source\'s 3rd party dashboard.<br />Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

        self.assertEqual(
            data_status[ad_group_source2.source_id]['message'],
            '<b>Bid CPC</b> for this Media Source differs from Bid CPC in the Media Source\'s 3rd party dashboard.<br /><b>Daily Budget</b> for this Media Source differs from Daily Budget in the Media Source\'s 3rd party dashboard.<br />Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

        self.assertEqual(
            data_status[ad_group_source3.source_id]['message'],
            'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

    def test_get_ad_group_sources_data_status_cannot_edit_cpc_budget(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=2)

        ad_group_settings = models.AdGroup.objects.get(id=1).get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings([ad_group_source])
        ad_group_sources_states = helpers.get_ad_group_sources_states([ad_group_source])

        # remove all available actions - this makes editing disabled
        ad_group_source.source.source_type.available_actions = []
        ad_group_source.source.source_type.save()

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child()

        data_status = helpers.get_data_status(
            [ad_group_source],
            helpers.get_last_sync_messages([ad_group_source], last_successful_sync_time),
            helpers.get_ad_group_sources_state_messages([ad_group_source],
                                                        ad_group_settings,
                                                        ad_group_sources_settings,
                                                        ad_group_sources_states)
        )

        self.assertEqual(
            data_status[ad_group_source.source_id]['message'],
            'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

    def test_get_ad_group_sources_data_status_not_stale(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=3)

        ad_group_settings = models.AdGroup.objects.get(id=1).get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings([ad_group_source])
        ad_group_sources_states = helpers.get_ad_group_sources_states([ad_group_source])

        last_sync = datetime.datetime.now()
        data_status = helpers.get_data_status(
            [ad_group_source],
            helpers.get_last_sync_messages([ad_group_source], {ad_group_source.id: last_sync}),
            helpers.get_ad_group_sources_state_messages([ad_group_source],
                                                        ad_group_settings,
                                                        ad_group_sources_settings,
                                                        ad_group_sources_states)
        )

        self.assertEqual(data_status[ad_group_source.source_id]['ok'], True)

        datetime_string = pytz.utc.localize(last_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))

        self.assertEqual(
            data_status[ad_group_source.source_id]['message'],
            'All data is OK. Last OK sync was on: <b>{}</b>'.format(
                datetime_string.strftime('%m/%d/%Y %-I:%M %p'))
        )

    def test_get_ad_group_sources_data_status_no_settings(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=4)

        ad_group_settings = models.AdGroup.objects.get(id=1).get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings([ad_group_source])
        ad_group_sources_states = helpers.get_ad_group_sources_states([ad_group_source])

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child()
        data_status = helpers.get_data_status(
            [ad_group_source],
            helpers.get_last_sync_messages([ad_group_source], last_successful_sync_time),
            helpers.get_ad_group_sources_state_messages([ad_group_source],
                                                        ad_group_settings,
                                                        ad_group_sources_settings,
                                                        ad_group_sources_states)
        )

        self.assertEqual(data_status[ad_group_source.source_id]['ok'], False)

        self.assertEqual(
            data_status[ad_group_source.source_id]['message'],
            'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

    def test_get_ad_group_sources_data_status_property_none(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=4)

        ad_group_settings = models.AdGroup.objects.get(id=1).get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings([ad_group_source])
        ad_group_sources_states = helpers.get_ad_group_sources_states([ad_group_source])

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child()
        data_status = helpers.get_data_status(
            [ad_group_source],
            helpers.get_last_sync_messages([ad_group_source], last_successful_sync_time),
            helpers.get_ad_group_sources_state_messages([ad_group_source],
                                                        ad_group_settings,
                                                        ad_group_sources_settings,
                                                        ad_group_sources_states)
        )

        self.assertEqual(data_status[ad_group_source.source_id]['ok'], False)

        self.assertEqual(
            data_status[ad_group_source.source_id]['message'],
            'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )

    def test_parse_get_request_array(self):
        self.assertEqual(helpers.parse_get_request_content_ad_ids({'ids': '1,2'}, 'ids'), [1, 2])
        with self.assertRaises(exc.ValidationError):
            helpers.parse_get_request_content_ad_ids({'ids': '1,a'}, 'ids')

    def test_parse_post_request_array(self):
        self.assertEqual(helpers.parse_post_request_content_ad_ids({'ids': ['1', '2']}, 'ids'), [1, 2])
        with self.assertRaises(exc.ValidationError):
            helpers.parse_post_request_content_ad_ids({'ids': ['1', 'a']}, 'ids')


class GetChangedContentAdsTestCase(TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ag = models.AdGroup.objects.get(id=2)
        self.sources = models.Source.objects.all()

    def test_get_content_ad_last_change_dt(self):
        last_change_dt = helpers.get_content_ad_last_change_dt(self.ag, self.sources)
        self.assertEqual(datetime.datetime(2015, 7, 1), last_change_dt)

        last_change_dt = helpers.get_content_ad_last_change_dt(self.ag, self.sources,
                                                               last_change_dt=datetime.datetime(2015, 7, 1))
        self.assertEqual(None, last_change_dt)

    def test_get_changed_content_ads(self):
        changed_content_ads = helpers.get_changed_content_ads(self.ag, self.sources)
        self.assertItemsEqual([
            models.ContentAd.objects.get(id=4),
            models.ContentAd.objects.get(id=5),
        ], changed_content_ads)

        changed_content_ads = helpers.get_changed_content_ads(self.ag, self.sources,
                                                              last_change_dt=datetime.datetime(2015, 2, 23))
        self.assertItemsEqual([
            models.ContentAd.objects.get(id=5),
        ], changed_content_ads)

        changed_content_ads = helpers.get_changed_content_ads(self.ag, self.sources,
                                                              last_change_dt=datetime.datetime(2015, 7, 1))
        self.assertItemsEqual([], changed_content_ads)


class GetSelectedContentAdsTest(TestCase):
    fixtures = ['test_api']

    def test_get_content_ads_all(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_all_disabled(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [2, 3])

    def test_get_content_ads_batch(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [1, 2])

    def test_get_content_ads_batch_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = [3]
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_batch_disabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [2])

    def test_get_content_ads_only_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = None
        content_ad_ids_selected = [1, 3]
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [1, 3])

    def test_get_content_ads_all_exclude_archived(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = False

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        self._assert_content_ads(content_ads, [1, 2])

    def _assert_content_ads(self, content_ads, expected_ids):
        self.assertQuerysetEqual(
            content_ads, expected_ids, transform=lambda ad: ad.id, ordered=False)


class SetAdGroupSourceTest(TestCase):

    fixtures = ['test_api']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User(id=1)

    def test_add_source_to_ad_group(self):
        ad_group_source_id = 2
        default_settings = models.DefaultSourceSettings.objects.get(pk=1)
        self.assertEqual(default_settings.source_id, ad_group_source_id)

        ad_group = models.AdGroup.objects.get(pk=10)
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)

        # ensure sources are not added before we actually try to add them
        self.assertFalse(ad_group_sources.exists())

        ad_group_source = helpers.add_source_to_ad_group(default_settings, ad_group)
        ad_group_source.save()

        self.assertTrue(ad_group_sources.count(), 1)

        ad_group_source = ad_group_sources[0]
        self.assertEqual(ad_group_source.source, default_settings.source)

    def test_set_ad_group_source_defaults(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=6)
        # target mobile
        ad_group_settings.target_devices = ['mobile']
        ad_group_settings.save(self.request)

        default_settings = models.DefaultSourceSettings.objects.get(pk=1)

        ad_group_source = helpers.add_source_to_ad_group(default_settings, ad_group_settings.ad_group)
        ad_group_source.save()

        helpers.set_ad_group_source_defaults(default_settings, ad_group_settings, ad_group_source, self.request)

        ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source)
        self.assertEqual(ad_group_source_settings.count(), 2)

        ad_group_source_settings = ad_group_source_settings.latest()
        self.assertEqual(ad_group_source_settings.daily_budget_cc, default_settings.daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, default_settings.mobile_cpc_cc)


