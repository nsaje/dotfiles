# -*- coding: utf-8 -*-
import datetime
import decimal

from django.core.exceptions import MultipleObjectsReturned
from django.http.request import HttpRequest
from django.test import RequestFactory
from django.test import TestCase
from mock import patch

from dash import constants
from dash import models
from dash import publisher_helpers
from dash.views import helpers
from utils import exc
from utils.test_helper import fake_request
from zemauth.models import User


class ViewHelpersTestCase(TestCase):
    fixtures = ["test_api.yaml"]

    def test_get_target_regions_string(self):
        regions = ["US", "501"]
        self.assertEqual(helpers.get_target_regions_string(regions), "United States, 501 New York, NY")

        regions = []
        self.assertEqual(helpers.get_target_regions_string(regions), "worldwide")

    def test_parse_get_request_array(self):
        self.assertEqual(helpers.parse_get_request_content_ad_ids({"ids": "1,2"}, "ids"), [1, 2])
        with self.assertRaises(exc.ValidationError):
            helpers.parse_get_request_content_ad_ids({"ids": "1,a"}, "ids")

    def test_parse_post_request_array(self):
        self.assertEqual(helpers.parse_post_request_ids({"ids": ["1", "2"]}, "ids"), [1, 2])
        with self.assertRaises(exc.ValidationError):
            helpers.parse_post_request_ids({"ids": ["1", "a"]}, "ids")


class GetChangedContentAdsTestCase(TestCase):
    fixtures = ["test_api"]

    def setUp(self):
        self.ag = models.AdGroup.objects.get(id=2)
        self.sources = models.Source.objects.all()

    def test_get_content_ad_last_change_dt(self):
        last_change_dt = helpers.get_content_ad_last_change_dt(self.ag, self.sources)
        self.assertEqual(datetime.datetime(2015, 7, 1), last_change_dt)

        last_change_dt = helpers.get_content_ad_last_change_dt(
            self.ag, self.sources, last_change_dt=datetime.datetime(2015, 7, 1)
        )
        self.assertEqual(None, last_change_dt)

    def test_get_changed_content_ads(self):
        changed_content_ads = helpers.get_changed_content_ads(self.ag, self.sources)
        self.assertCountEqual(
            [models.ContentAd.objects.get(id=4), models.ContentAd.objects.get(id=5)], changed_content_ads
        )

        changed_content_ads = helpers.get_changed_content_ads(
            self.ag, self.sources, last_change_dt=datetime.datetime(2015, 2, 23)
        )
        self.assertCountEqual([models.ContentAd.objects.get(id=5)], changed_content_ads)

        changed_content_ads = helpers.get_changed_content_ads(
            self.ag, self.sources, last_change_dt=datetime.datetime(2015, 7, 1)
        )
        self.assertCountEqual([], changed_content_ads)


class GetSelectedEntityTest(TestCase):
    fixtures = ["test_api"]

    def test_get_content_ads_all(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_all_disabled(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [2, 3])

    def test_get_content_ads_batch(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [1, 2])

    def test_get_content_ads_batch_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = [3]
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_batch_disabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_selected = []
        content_ad_ids_not_selected = [1]
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [2])

    def test_get_content_ads_only_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = None
        content_ad_ids_selected = [1, 3]
        content_ad_ids_not_selected = []
        include_archived = True

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [1, 3])

    def test_get_content_ads_all_exclude_archived(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_selected = []
        content_ad_ids_not_selected = []
        include_archived = False

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [1, 2])

    def test_only_allowed_entities(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 2
        content_ad_ids_selected = [6]
        content_ad_ids_not_selected = []
        include_archived = False

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        self._assert_content_ads(content_ads, [])

    @patch("dash.views.helpers.get_selected_entities")
    def test_get_selected_entities_post_request(self, mock_get_selected_entities):
        objects = "test_objects"
        data = {"select_all": True, "select_batch": 3, "selected_ids": ["1", "2"], "not_selected_ids": ["3", "4"]}

        ret = helpers.get_selected_entities_post_request(objects, data, include_archived=True, ad_group_id=1)

        mock_get_selected_entities.assert_called_once_with(objects, True, [1, 2], [3, 4], True, 3, ad_group_id=1)
        self.assertEqual(ret, mock_get_selected_entities.return_value)

    def test_get_selected_adgroup_sources(self):
        data = {"select_all": False, "selected_ids": ["1", "2"]}
        ad_group_id = 1

        adgroup_sources = helpers.get_selected_adgroup_sources(
            models.AdGroupSource.objects, data, ad_group_id=ad_group_id
        )

        self.assertTrue(all(adgroup_source.ad_group_id == ad_group_id for adgroup_source in adgroup_sources))
        self.assertCountEqual([1, 2], [adgroup_source.id for adgroup_source in adgroup_sources])

    def _assert_content_ads(self, content_ads, expected_ids):
        self.assertQuerysetEqual(content_ads, expected_ids, transform=lambda ad: ad.id, ordered=False)


class AdGroupSourceTableEditableFieldsTest(TestCase):
    fixtures = ["test_api.yaml"]

    class DatetimeMock(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 6, 5, 13, 22, 23)

    def test_get_editable_fields_status_setting_enabled(self):
        req = RequestFactory().get("/")
        req.user = User.objects.get(pk=1)

        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.supports_retargeting = True
        ad_group_source.source.save()

        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.ad_group.save(req)

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": True, "message": None})

    def test_get_editable_fields_status_setting_no_fb_account(self):
        req = RequestFactory().get("/")
        req.user = User.objects.get(pk=1)

        source = models.Source.objects.get(pk=10)
        source.supports_retargeting = True

        ad_group_source = models.AdGroupSource.objects.get(pk=12)
        ad_group_source.source = source
        ad_group_source.can_manage_content_ads = True

        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.ad_group.save(req)

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result, {"enabled": False, "message": "Please connect your Facebook page to add Facebook as media source."}
        )

    def test_get_editable_fields_status_setting_yahoo_cpc_too_low(self):
        req = RequestFactory().get("/")
        req.user = User.objects.get(pk=1)

        source = models.Source.objects.get(pk=5)
        source.supports_retargeting = True
        source.source_type.min_cpc = decimal.Decimal("0.1")

        ad_group_source = models.AdGroupSource.objects.get(pk=12)
        ad_group_source.source = source
        ad_group_source.can_manage_content_ads = True
        ad_group_source.save()

        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.ad_group_source = ad_group_source
        ad_group_source_settings.cpc_cc = 0.05
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_devices = [constants.AdTargetDevice.DESKTOP]

        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.ad_group.save(req)

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This source can not be enabled with the current settings - CPC too low for desktop targeting.",
            },
        )

    def test_get_editable_fields_status_setting_yahoo_cpm_too_low(self):
        req = RequestFactory().get("/")
        req.user = User.objects.get(pk=1)

        source = models.Source.objects.get(pk=5)
        source.supports_retargeting = True
        source.source_type.min_cpm = decimal.Decimal("0.1")

        ad_group_source = models.AdGroupSource.objects.get(pk=12)
        ad_group_source.source = source
        ad_group_source.can_manage_content_ads = True
        ad_group_source.save()

        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.ad_group_source = ad_group_source
        ad_group_source_settings.cpm = 0.20

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.ad_group.bidding_type = constants.BiddingType.CPM

        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.ad_group.save(req)

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {"enabled": False, "message": "This source can not be enabled with the current settings - CPM too low."},
        )

    def test_get_editable_fields_status_setting_max_cpm(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source.source.supports_retargeting = True
        ad_group_source.source.save()

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.max_cpm = decimal.Decimal("1.5")

        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_STATE,
            constants.SourceAction.CAN_SET_MAX_CPM,
        ]

        allowed_sources = set([ad_group_source.source_id])
        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": True, "message": None})

        ad_group_source.source.source_type.available_actions.remove(constants.SourceAction.CAN_SET_MAX_CPM)
        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This source can not be enabled because it does not support max CPM restriction.",
            },
        )

    def test_get_editable_fields_without_retargeting(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {"enabled": False, "message": "This source can not be enabled because it does not support retargeting."},
        )

        ad_group_settings.retargeting_ad_groups = []
        ad_group_settings.audience_targeting = [100, 200]
        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {"enabled": False, "message": "This source can not be enabled because it does not support retargeting."},
        )

    def test_get_editable_fields_status_not_in_allowed_sources(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.supports_retargeting = True
        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": True, "message": None})

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, set()
        )
        self.assertEqual(result, {"enabled": False, "message": "Please contact support to enable this source."})

    def test_get_editable_fields_status_setting_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": False, "message": "This source must be managed manually."})

    def test_get_editable_fields_status_setting_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.source.maintenance = True

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": False, "message": "This source is currently in maintenance mode."})

    def test_get_editable_fields_status_setting_no_cms_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        allowed_sources = set([ad_group_source.source_id])

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        ad_group_source.can_manage_content_ads = False

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": False, "message": "Please contact support to enable this source."})

    def test_get_editable_fields_status_setting_no_dma_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        allowed_sources = set([ad_group_source.source_id])

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_regions = ["693"]

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {"enabled": False, "message": "This source can not be enabled because it does not support DMA targeting."},
        )

    def test_get_editable_fields_status_setting_no_subdivision_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        allowed_sources = set([ad_group_source.source_id])

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_regions = ["US-IL"]

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This source can not be enabled because it does not support U.S. state targeting.",
            },
        )

    def test_get_editable_fields_status_setting_no_dma_nor_subdivision_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        allowed_sources = set([ad_group_source.source_id])

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_regions = ["693", "US-IL"]

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This source can not be enabled because it does not support DMA and U.S. state targeting.",
            },
        )

    def test_get_editable_fields_status_setting_no_manual_target_regions_action(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        allowed_sources = set([ad_group_source.source_id])

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_regions = ["693"]

        ad_group_source.source.supports_retargeting = True
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_STATE,
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL,
        ]
        for adgs_settings in models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source):
            new_adgs_settings = adgs_settings.copy_settings()
            new_adgs_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
            new_adgs_settings.save(None)

        result = helpers._get_editable_fields_status_setting(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, adgs_settings, allowed_sources
        )

        self.assertEqual(result, {"enabled": True, "message": None})

    def test_get_editable_fields_bid_cpc_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPC]

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(result, {"enabled": True, "message": None})

    def test_get_editable_fields_bid_cpc_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This media source doesn't support setting this value through the dashboard.",
            },
        )

    def test_get_editable_fields_bid_cpc_adgroup_cpc_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the ad group is on Autopilot."}
        )

    def test_get_editable_fields_bid_cpc_adgroup_budget_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the ad group is on Autopilot."}
        )

    def test_get_editable_fields_bid_cpc_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPC]
        ad_group_source.source.maintenance = True

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This value cannot be edited because the media source is currently in maintenance.",
            },
        )

    def test_get_editable_fields_bid_cpc_campaign_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()
        campaign_settings.update_unsafe(None, autopilot=True)

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpc(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the campaign is on Autopilot."}
        )

    def test_get_editable_fields_bid_cpm_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPM]

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(result, {"enabled": True, "message": None})

    def test_get_editable_fields_bid_cpm_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {"enabled": False, "message": "This source can not be enabled because it does not support CPM buying."},
        )

    def test_get_editable_fields_bid_cpm_adgroup_cpm_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the ad group is on Autopilot."}
        )

    def test_get_editable_fields_bid_cpm_adgroup_budget_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the ad group is on Autopilot."}
        )

    def test_get_editable_fields_bid_cpm_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPM]
        ad_group_source.source.maintenance = True

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This value cannot be edited because the media source is currently in maintenance.",
            },
        )

    def test_get_editable_fields_bid_cpm_campaign_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()
        campaign_settings.update_unsafe(None, autopilot=True)

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_bid_cpm(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the campaign is on Autopilot."}
        )

    def test_get_editable_fields_daily_budget_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC
        ]

        result = helpers._get_editable_fields_daily_budget(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(result, {"enabled": True, "message": None})

    def test_get_editable_fields_daily_budget_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_daily_budget(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This media source doesn't support setting this value through the dashboard.",
            },
        )

    def test_get_editable_fields_daily_budget_adgroup_budget_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        ad_group_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_daily_budget(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the ad group is on Autopilot."}
        )

    def test_get_editable_fields_daily_budget_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()

        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC
        ]
        ad_group_source.source.maintenance = True

        result = helpers._get_editable_fields_daily_budget(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result,
            {
                "enabled": False,
                "message": "This value cannot be edited because the media source is currently in maintenance.",
            },
        )

    def test_get_editable_fields_daily_budget_campaign_autopilot(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None
        campaign_settings = ad_group_source.ad_group.campaign.get_current_settings()
        campaign_settings.update_unsafe(None, autopilot=True)

        ad_group_source.source.source_type.available_actions = []

        result = helpers._get_editable_fields_daily_budget(
            ad_group_source.ad_group, ad_group_source, ad_group_settings, campaign_settings
        )

        self.assertEqual(
            result, {"enabled": False, "message": "This value cannot be edited because the campaign is on Autopilot."}
        )


class SetAdGroupSourceTest(TestCase):

    fixtures = ["test_api"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.META["SERVER_NAME"] = "testname"
        self.request.META["SERVER_PORT"] = 1234
        self.request.user = User(id=1)

    def prepare_ad_group_source(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=6)
        source_settings = models.DefaultSourceSettings.objects.get(pk=1)
        ad_group_settings.ad_group.campaign.account.allowed_sources.add(source_settings.source)
        ad_group_source = models.AdGroupSource.objects.create(
            None, ad_group_settings.ad_group, source_settings.source, write_history=False, k1_sync=False
        )
        return ad_group_source, source_settings

    def test_set_ad_group_source_settings_mobile(self):
        ad_group_source, source_settings = self.prepare_ad_group_source()
        new_ad_group_settings = ad_group_source.ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.target_devices = [constants.AdTargetDevice.MOBILE]
        new_ad_group_settings.save(None)

        ad_group_source.set_initial_settings(self.request, ad_group_source.ad_group)

        ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source)

        ad_group_source_settings = ad_group_source_settings.latest()
        self.assertEqual(ad_group_source_settings.daily_budget_cc, source_settings.source.default_daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, source_settings.source.default_mobile_cpc_cc)
        self.assertEqual(ad_group_source_settings.cpm, source_settings.source.default_mobile_cpm)
        self.assertEqual(ad_group_source_settings.state, constants.AdGroupSourceSettingsState.ACTIVE)

    def test_set_ad_group_source_settings_desktop(self):
        ad_group_source, source_settings = self.prepare_ad_group_source()
        ad_group_source.set_initial_settings(
            self.request, ad_group_source.ad_group, state=constants.AdGroupSourceSettingsState.INACTIVE
        )

        ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source)

        ad_group_source_settings = ad_group_source_settings.latest()
        self.assertEqual(ad_group_source_settings.daily_budget_cc, source_settings.source.default_daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, ad_group_source.source.default_cpc_cc)
        self.assertEqual(ad_group_source_settings.cpm, ad_group_source.source.default_cpm)
        self.assertEqual(ad_group_source_settings.state, constants.AdGroupSourceSettingsState.INACTIVE)


class PublisherHelpersTest(TestCase):
    fixtures = ["test_api"]

    def test_publisher_exchange(self):
        adiant_source = models.Source.objects.get(pk=7)
        self.assertEqual("b1_adiant", adiant_source.tracking_slug)
        self.assertEqual("adiant", publisher_helpers.publisher_exchange(adiant_source))

        outbrain_source = models.Source.objects.get(pk=3)
        self.assertEqual("outbrain", outbrain_source.tracking_slug)
        self.assertEqual("outbrain", publisher_helpers.publisher_exchange(outbrain_source))

    def test_publisher_domain(self):
        self.assertTrue(publisher_helpers.is_publisher_domain("test.com"))
        self.assertTrue(publisher_helpers.is_publisher_domain("funky.co.uk"))

        self.assertFalse(publisher_helpers.is_publisher_domain("Happy Faces"))
        self.assertFalse(publisher_helpers.is_publisher_domain("贝客悦读 • 天涯之家HD"))
        self.assertFalse(publisher_helpers.is_publisher_domain("BS Local (CBS Local)"))
        self.assertFalse(publisher_helpers.is_publisher_domain("CNN Money (Turner U.S.)"))


class UtilityHelpers(TestCase):
    fixtures = ["test_views.yaml", "test_agency.yaml", "test_facebook.yaml"]

    def test_get_user_agency(self):
        u = User.objects.get(pk=1000)
        self.assertIsNone(helpers.get_user_agency(u))

        # add user to agency
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(u)

        self.assertEqual(agency, helpers.get_user_agency(u))

        other_agency = models.Agency(name="Random agency")
        other_agency.save(fake_request(u))
        other_agency.users.add(u)

        with self.assertRaises(MultipleObjectsReturned):
            helpers.get_user_agency(u)

    def test_is_agency_manager(self):
        acc = models.Account.objects.get(pk=1000)
        u = User.objects.get(pk=1000)

        acc.agency = None
        acc.save(fake_request(u))

        self.assertFalse(helpers.is_agency_manager(u, acc))

        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(u))

        self.assertFalse(helpers.is_agency_manager(u, acc))

        agency.users.add(u)
        self.assertTrue(helpers.is_agency_manager(u, acc))

    def test_is_agency_manager_fail(self):
        acc = models.Account.objects.get(pk=1000)
        u = User.objects.get(pk=1000)

        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(u))

        other_agency = models.Agency(name="Random agency")
        other_agency.save(fake_request(u))
        other_agency.users.add(u)

        self.assertFalse(helpers.is_agency_manager(u, acc), msg="account and user agency differ")

    def test_check_facebook_source_valid(self):
        non_fb_ad_group_source = models.AdGroupSource.objects.get(pk=100)
        result = helpers.check_facebook_source(non_fb_ad_group_source)
        self.assertTrue(result)

        fb_ad_group_source = models.AdGroupSource.objects.get(pk=200)
        result = helpers.check_facebook_source(fb_ad_group_source)
        self.assertTrue(result)

    def test_check_facebook_source_invalid(self):
        fb_ad_group_source = models.AdGroupSource.objects.get(pk=300)

        result = helpers.check_facebook_source(fb_ad_group_source)
        self.assertFalse(result)


class ValidateAdGroupsStateTest(TestCase):
    fixtures = ["test_views.yaml"]

    def test_ad_group_state_invalid(self):
        ad_groups = models.AdGroup.objects.filter(pk=987)
        campaign = ad_groups[0].campaign
        campaign_settings = campaign.get_current_settings()

        with self.assertRaises(exc.ValidationError):
            helpers.validate_ad_groups_state(ad_groups, campaign, campaign_settings, -1)

    @patch("dash.dashapi.data_helper.campaign_has_available_budget")
    def test_ad_group_state_has_budget(self, campaign_has_budget_mock):
        campaign_has_budget_mock.return_value = False

        ad_groups = models.AdGroup.objects.filter(pk=987)
        campaign = ad_groups[0].campaign
        campaign_settings = campaign.get_current_settings()
        state = constants.AdGroupSettingsState.ACTIVE

        models.CampaignGoal(campaign=campaign).save()

        with self.assertRaises(exc.ValidationError):
            helpers.validate_ad_groups_state(ad_groups, campaign, campaign_settings, state)

    @patch("dash.dashapi.data_helper.campaign_has_available_budget")
    def test_ad_group_state_no_goal(self, campaign_has_budget_mock):
        campaign_has_budget_mock.return_value = True

        ad_groups = models.AdGroup.objects.filter(pk=987)
        campaign = ad_groups[0].campaign
        campaign_settings = campaign.get_current_settings()
        state = constants.AdGroupSettingsState.ACTIVE

        with self.assertRaises(exc.ValidationError):
            helpers.validate_ad_groups_state(ad_groups, campaign, campaign_settings, state)
