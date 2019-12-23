from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import alerts


class AlertsTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user(permissions=["can_use_creative_icon"])

    def test_account_level_no_account_default_icon(self):
        account = magic_mixer.blend(core.models.Account)
        account_alerts = alerts.get_account_alerts(self.request, account)
        self.assertEqual(
            {
                "type": "danger",
                "message": "Please add a brand logo to this account. "
                + "The logo will be added to your ads if required by media source. "
                + "Logo can be added on account-level settings. "
                + "Read more about brand logo "
                + "<a href='https://help.zemanta.com/article/show/100808-adding-brand-logo-to-content-ads'>here</a>.",
            },
            account_alerts[0],
        )

    def test_account_level_no_account_default_icon_no_permission(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        account_alerts = alerts.get_account_alerts(request, account)
        self.assertEqual([], account_alerts)

    def test_account_level_with_account_default_icon(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        account_alerts = alerts.get_account_alerts(self.request, account)
        self.assertFalse(account_alerts)

    def test_campaign_level_no_account_default_icon(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_alerts = alerts.get_campaign_alerts(self.request, campaign)
        self.assertEqual(
            {
                "type": "danger",
                "message": "Please add a brand logo to this account. "
                + "The logo will be added to your ads if required by media source. "
                + "Logo can be added on account-level settings. "
                + "Read more about brand logo "
                + "<a href='https://help.zemanta.com/article/show/100808-adding-brand-logo-to-content-ads'>here</a>.",
            },
            campaign_alerts[0],
        )

    def test_campaign_level_no_account_default_icon_no_permission(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_alerts = alerts.get_campaign_alerts(request, campaign)
        self.assertEqual([], campaign_alerts)

    def test_campaign_level_with_account_default_icon(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_alerts = alerts.get_campaign_alerts(self.request, campaign)
        self.assertFalse(campaign_alerts)
