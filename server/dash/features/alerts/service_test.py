import datetime

from django.test import TestCase

import core.models
import dash.constants
import stats.constants
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import service


class AlertsServiceTestCase(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user(permissions=["can_use_placement_targeting"])

    def test_account_level_no_account_default_icon(self):
        account = magic_mixer.blend(core.models.Account)
        account_alerts = service.get_account_alerts(self.request, account)
        self.assertEqual(
            {
                "type": dash.constants.AlertType.DANGER,
                "message": service.ACCOUNT_DEFAULT_ICON_ALERT,
                "is_closable": True,
            },
            account_alerts[0],
        )

    def test_account_level_with_account_default_icon(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        account_alerts = service.get_account_alerts(self.request, account)
        self.assertEqual([], account_alerts)

    def test_account_level_with_placement_conversion_alert(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        account_alerts = service.get_account_alerts(
            self.request, account, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual(
            {
                "type": dash.constants.AlertType.WARNING,
                "message": service.PLACEMENT_CONVERSIONS_ALERT,
                "is_closable": True,
            },
            account_alerts[0],
        )

        start_date = datetime.datetime.strptime(service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d").date()
        account_alerts = service.get_account_alerts(
            self.request, account, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], account_alerts)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() + datetime.timedelta(days=1)
        account_alerts = service.get_account_alerts(
            self.request, account, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], account_alerts)

    def test_account_level_no_placement_conversion_alert_no_permission(self):
        test_helper.remove_permissions(self.request.user, ["can_use_placement_targeting"])

        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        account_alerts = service.get_account_alerts(
            self.request, account, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )

        self.assertEqual([], account_alerts)

    def test_campaign_level_no_account_default_icon(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_alerts = service.get_campaign_alerts(self.request, campaign)
        self.assertEqual(
            {
                "type": dash.constants.AlertType.DANGER,
                "message": service.ACCOUNT_DEFAULT_ICON_ALERT,
                "is_closable": True,
            },
            campaign_alerts[0],
        )

    def test_campaign_level_with_account_default_icon(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_alerts = service.get_campaign_alerts(self.request, campaign)
        self.assertEqual([], campaign_alerts)

    def test_campaign_level_with_placement_conversion_alert(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        campaign_alerts = service.get_campaign_alerts(
            self.request, campaign, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual(
            {
                "type": dash.constants.AlertType.WARNING,
                "message": service.PLACEMENT_CONVERSIONS_ALERT,
                "is_closable": True,
            },
            campaign_alerts[0],
        )

        start_date = datetime.datetime.strptime(service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d").date()
        campaign_alerts = service.get_campaign_alerts(
            self.request, campaign, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], campaign_alerts)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() + datetime.timedelta(days=1)
        campaign_alerts = service.get_campaign_alerts(
            self.request, campaign, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], campaign_alerts)

    def test_campaign_level_no_placement_conversion_alert_no_permission(self):
        test_helper.remove_permissions(self.request.user, ["can_use_placement_targeting"])

        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        campaign_alerts = service.get_campaign_alerts(
            self.request, campaign, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )

        self.assertEqual([], campaign_alerts)

    def test_ad_group_level_no_account_default_icon(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_alerts = service.get_ad_group_alerts(self.request, ad_group)
        self.assertEqual(
            {
                "type": dash.constants.AlertType.DANGER,
                "message": service.ACCOUNT_DEFAULT_ICON_ALERT,
                "is_closable": True,
            },
            ad_group_alerts[0],
        )

    def test_ad_group_level_with_account_default_icon(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_alerts = service.get_ad_group_alerts(self.request, ad_group)
        self.assertEqual([], ad_group_alerts)

    def test_ad_group_level_with_placement_conversion_alert(self):
        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        ad_group_alerts = service.get_ad_group_alerts(
            self.request, ad_group, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual(
            {
                "type": dash.constants.AlertType.WARNING,
                "message": service.PLACEMENT_CONVERSIONS_ALERT,
                "is_closable": True,
            },
            ad_group_alerts[0],
        )

        start_date = datetime.datetime.strptime(service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d").date()
        ad_group_alerts = service.get_ad_group_alerts(
            self.request, ad_group, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], ad_group_alerts)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() + datetime.timedelta(days=1)
        ad_group_alerts = service.get_ad_group_alerts(
            self.request, ad_group, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )
        self.assertEqual([], ad_group_alerts)

    def test_ad_group_level_no_placement_conversion_alert_no_permission(self):
        test_helper.remove_permissions(self.request.user, ["can_use_placement_targeting"])

        icon = magic_mixer.blend(core.models.ImageAsset)
        account = magic_mixer.blend(core.models.Account)
        account.settings.update_unsafe(None, default_icon=icon)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        start_date = datetime.datetime.strptime(
            service.PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d"
        ).date() - datetime.timedelta(days=1)
        ad_group_alerts = service.get_ad_group_alerts(
            self.request, ad_group, breakdown=stats.constants.DimensionIdentifier.PLACEMENT, start_date=start_date
        )

        self.assertEqual([], ad_group_alerts)
