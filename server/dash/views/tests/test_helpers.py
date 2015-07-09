import datetime
import pytz

from django.test import TestCase
from django.conf import settings

import actionlog.sync
from dash.views import helpers
from dash import models
from dash import constants

from utils import exc


class ViewHelpersTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_get_ad_group_sources_last_sync_messages(self):
        ad_group_sources = models.AdGroupSource.objects.filter(pk__in=[1, 2, 3])

        last_successful_ags_sync_times = {}
        for ags in ad_group_sources:
            last_successful_ags_sync_times.update(
                actionlog.sync.AdGroupSourceSync(ags).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(ad_group_sources, last_successful_ags_sync_times)
        self.assertEqual(len(last_sync_messages), 3)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for ags in ad_group_sources:
            last_successful_source_sync_times.update(
                actionlog.sync.AdGroupSourceSync(ags).get_latest_source_success(recompute=False)
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
                actionlog.sync.AdGroupSync(ag).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(ad_groups, last_successful_ad_group_sync_times)
        self.assertEqual(len(last_sync_messages), 2)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for ag in ad_groups:
            last_successful_source_sync_times.update(
                actionlog.sync.AdGroupSync(ag).get_latest_source_success(recompute=False)
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 6)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[4], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[5], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_ad_groups = models.AdGroup.objects.filter(pk__in=[5])
        last_successful_archived_sync_times = {}
        for ad_group in archived_ad_groups:
            last_successful_archived_sync_times.update(
                actionlog.sync.AdGroupSync(ad_group).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(archived_ad_groups, last_successful_archived_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[5], ([], True))

    def test_get_campaign_last_sync_messages(self):
        campaigns = models.Campaign.objects.filter(pk__in=[1, 2])

        last_successful_campaign_sync_times = {}
        for campaign in campaigns:
            last_successful_campaign_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(campaigns, last_successful_campaign_sync_times)
        self.assertEqual(len(last_sync_messages), 2)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for campaign in campaigns:
            last_successful_source_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_source_success(recompute=False)
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 6)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_campaigns = models.Campaign.objects.filter(pk__in=[4])
        last_successful_archived_sync_times = {}
        for campaign in archived_campaigns:
            last_successful_archived_sync_times.update(
                actionlog.sync.CampaignSync(campaign).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(archived_campaigns, last_successful_archived_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[4], ([], True))

    def test_get_account_last_sync_messages(self):
        accounts = models.Account.objects.filter(pk__in=[1])

        last_successful_account_sync_times = {}
        for account in accounts:
            last_successful_account_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_success_by_child(recompute=False)
            )

        last_sync_messages = helpers.get_last_sync_messages(accounts, last_successful_account_sync_times)
        self.assertEqual(len(last_sync_messages), 1)
        self.assertEquals(last_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        last_successful_source_sync_times = {}
        for account in accounts:
            last_successful_source_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_source_success(recompute=False)
            )

        sources = models.Source.objects.filter(pk__in=last_successful_source_sync_times.keys())
        last_source_sync_messages = helpers.get_last_sync_messages(sources, last_successful_source_sync_times)
        self.assertEqual(len(last_source_sync_messages), 6)
        self.assertEquals(last_source_sync_messages[1], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[2], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))
        self.assertEquals(last_source_sync_messages[3], (['Last OK sync was on: <b>06/10/2014 5:58 AM</b>'], False))

        archived_accounts = models.Account.objects.filter(pk__in=[3])
        last_successful_archived_sync_times = {}
        for account in archived_accounts:
            last_successful_archived_sync_times.update(
                actionlog.sync.AccountSync(account).get_latest_success_by_child(recompute=False)
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
                actionlog.sync.AdGroupSourceSync(ags).get_latest_success_by_child(recompute=False)
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

        # clear all available actions - this makes editing disabled
        ad_group_source.source.source_type.available_actions.clear()

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child(
            recompute=False
        )

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

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child(
            recompute=False
        )
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

        last_successful_sync_time = actionlog.sync.AdGroupSourceSync(ad_group_source).get_latest_success_by_child(
            recompute=False
        )
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


class GetSelectedContentAdsTest(TestCase):
    fixtures = ['test_api']

    def test_get_content_ads_all(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_all_disabled(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [2, 3])

    def test_get_content_ads_batch(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [1, 2])

    def test_get_content_ads_batch_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = [3]
        content_ad_ids_not_selected = []

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_batch_disabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [2])

    def test_get_content_ads_only_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = None
        content_ad_ids_selected = [1, 3]
        content_ad_ids_not_selected = []

        content_ads = helpers.get_selected_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected)

        self._assert_content_ads(content_ads, [1, 3])

    def _assert_content_ads(self, content_ads, expected_ids):
        self.assertQuerysetEqual(
            content_ads, expected_ids, transform=lambda ad: ad.id, ordered=False)
