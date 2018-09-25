import decimal
from mock import patch

from django.test import TestCase
from utils.magic_mixer import magic_mixer
from dash import constants

import core.entity
import core.source

import utils.exc


@patch("utils.k1_helper.update_ad_group")
@patch("dash.views.helpers.get_source_initial_state", lambda x: True)
class AdGroupSourceCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.default_source_settings = magic_mixer.blend(
            core.source.DefaultSourceSettings, source__maintenance=False, credentials=magic_mixer.RANDOM
        )
        self.ad_group = magic_mixer.blend(
            core.entity.AdGroup, campaign__account__allowed_sources=[self.default_source_settings.source]
        )

    def test_create(self, mock_k1):
        ad_group_source = core.entity.AdGroupSource.objects.create(
            self.request, self.ad_group, self.default_source_settings.source
        )

        self.assertEqual(ad_group_source.source, self.default_source_settings.source)
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source
        ).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_create_with_update(self, mock_k1):
        ad_group_source = core.entity.AdGroupSource.objects.create(
            self.request,
            self.ad_group,
            self.default_source_settings.source,
            state=constants.AdGroupSourceSettingsState.INACTIVE,
            cpc_cc=decimal.Decimal("0.13"),
            cpm=decimal.Decimal("1.13"),
            daily_budget_cc=decimal.Decimal("5.2"),
        )

        self.assertEqual(ad_group_source.source, self.default_source_settings.source)
        self.assertTrue(mock_k1.called)

        new_settings = ad_group_source.get_current_settings()
        self.assertEqual(constants.AdGroupSourceSettingsState.INACTIVE, new_settings.state)
        self.assertEqual(decimal.Decimal("0.13"), new_settings.cpc_cc)
        self.assertEqual(decimal.Decimal("1.13"), new_settings.cpm)
        self.assertEqual(decimal.Decimal("5.2"), new_settings.daily_budget_cc)

    def test_create_already_exists(self, mock_k1):
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=self.default_source_settings.source)

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(self.request, self.ad_group, self.default_source_settings.source)

    def test_create_on_video_campaign(self, mock_k1):
        self.ad_group.campaign.type = constants.CampaignType.VIDEO
        self.ad_group.campaign.save()

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(self.request, self.ad_group, self.default_source_settings.source)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_create_ad_review_only_already_exists(self, mock_autopilot, mock_k1):
        ad_group_source = magic_mixer.blend(
            core.entity.AdGroupSource,
            ad_group=self.ad_group,
            source=self.default_source_settings.source,
            ad_review_only=True,
        )
        ad_group_source.settings.update(state=constants.AdGroupSourceSettingsState.INACTIVE)
        core.entity.AdGroupSource.objects.create(self.request, self.ad_group, self.default_source_settings.source)

        ad_group_source = core.entity.AdGroupSource.objects.get()
        self.assertFalse(ad_group_source.ad_review_only)
        self.assertEqual(constants.AdGroupSourceSettingsState.ACTIVE, ad_group_source.settings.state)

    def test_create_not_on_account(self, mock_k1):
        self.ad_group.campaign.account.allowed_sources.remove(self.default_source_settings.source)

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(self.request, self.ad_group, self.default_source_settings.source)

    @patch("dash.retargeting_helper.can_add_source_with_retargeting")
    def test_create_retargeting(self, mock_retargeting, mock_k1):
        mock_retargeting.return_value = False

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(self.request, self.ad_group, self.default_source_settings.source)

        mock_retargeting.assert_called_once_with(
            self.default_source_settings.source, self.ad_group.get_current_settings()
        )

    def test_bulk_create_on_allowed_sources(self, mock_k1):
        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, self.ad_group, write_history=False
        )

        self.assertEqual([x.source for x in ad_group_sources], [self.default_source_settings.source])
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=self.ad_group
        ).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_bulk_create_on_allowed_sources_maintenance(self, mock_k1):
        self.default_source_settings.source.maintenance = True
        self.default_source_settings.source.save()
        request = magic_mixer.blend_request_user()

        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            request, self.ad_group, write_history=False
        )

        self.assertCountEqual(ad_group_sources, [])
        self.assertFalse(mock_k1.called)

    def test_bulk_create_on_video_sources(self, mock_k1):
        self.default_source_settings.source.supports_video = True
        self.default_source_settings.source.save()
        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, self.ad_group, write_history=False
        )
        self.assertEqual([x.source for x in ad_group_sources], [self.default_source_settings.source])
        self.assertTrue(mock_k1.called)

    def test_video_campaign_bulk_create_on_video_sources(self, mock_k1):
        self.default_source_settings.source.supports_video = True
        self.default_source_settings.source.save()
        self.ad_group.campaign.type = constants.CampaignType.VIDEO
        self.ad_group.campaign.save()
        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, self.ad_group, write_history=False
        )
        self.assertEqual([x.source for x in ad_group_sources], [self.default_source_settings.source])
        self.assertTrue(mock_k1.called)

    def test_video_campaign_bulk_create_on_content_sources(self, mock_k1):
        self.ad_group.campaign.type = constants.CampaignType.VIDEO
        self.ad_group.campaign.save()
        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, self.ad_group, write_history=False
        )
        self.assertCountEqual(ad_group_sources, [])
        self.assertFalse(mock_k1.called)


@patch("utils.k1_helper.update_ad_group")
class AdGroupSourceClone(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_clone(self, mock_k1):
        source_ad_group_source = magic_mixer.blend(
            core.entity.AdGroupSource, source=magic_mixer.blend_source_w_defaults()
        )
        source_ad_group_source.settings.update_unsafe(
            None,
            daily_budget_cc=decimal.Decimal("5"),
            cpc_cc=decimal.Decimal("0.1"),
            cpm=decimal.Decimal("1.1"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        ad_group = magic_mixer.blend(core.entity.AdGroup)

        ad_group_source = core.entity.AdGroupSource.objects.clone(
            magic_mixer.blend_request_user(), ad_group, source_ad_group_source
        )

        ad_group_source_settings = ad_group_source.get_current_settings()
        self.assertEqual(ad_group_source.source, source_ad_group_source.source)
        self.assertEqual(ad_group_source_settings.daily_budget_cc, source_ad_group_source.settings.daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, source_ad_group_source.settings.cpc_cc)
        self.assertEqual(ad_group_source_settings.cpm, source_ad_group_source.settings.cpm)

        self.assertTrue(mock_k1.called)


class MigrateToBcmV2Test(TestCase):
    def test_migrate_to_bcm_v2(self):
        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group)

        request = magic_mixer.blend_request_user()
        ad_group_source.settings.update(
            request=request,
            k1_sync=False,
            system_user=None,
            skip_automation=True,
            skip_validation=True,
            skip_notification=True,
            daily_budget_cc=decimal.Decimal("10"),
            cpc_cc=decimal.Decimal("0.32"),
        )

        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        ad_group_source.migrate_to_bcm_v2(request, decimal.Decimal("0.2"), decimal.Decimal("0.1"))

        ad_group_source_settings = ad_group_source.get_current_settings()
        self.assertEqual(14, ad_group_source_settings.daily_budget_cc)
        self.assertEqual(decimal.Decimal("0.444"), ad_group_source_settings.cpc_cc)
