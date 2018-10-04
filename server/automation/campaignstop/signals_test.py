import decimal
from mock import patch

from django.test import TestCase

import core.features.bcm
import core.models
import core.models.settings
import dash.constants

from . import signals

from utils.magic_mixer import magic_mixer
from utils import dates_helper


class NotifyBudgetsTest(TestCase):
    def setUp(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.3333"),
        )
        self.budget = magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=credit,
            amount=decimal.Decimal("200"),
            margin=0,
        )

        signals.connect_notify_budgets()
        self.addCleanup(signals.disconnect_notify_budgets)

    @patch("automation.campaignstop.service.update_notifier.notify_budget_line_item_change")
    def test_notify_budget_line_item_change(self, mock_notify):
        self.budget.amount = self.budget.amount + 1
        self.budget.save()
        mock_notify.assert_called_with(self.budget.campaign)


class NotifyAdGroupSettingsChangeTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        signals.connect_notify_ad_group_settings_change()

    # @patch("automation.campaignstop.service.update_notifier.notify_ad_group_settings_change")
    # def test_notify_ad_group_settings_change(self, mock_notify):
    #     changes = {"end_date": dates_helper.local_today()}
    #     self.ad_group.settings.update(None, **changes)
    #     mock_notify.assert_called_with(ANY, changes)


class NotifyAdGroupSourceSettingsChangeTest(TestCase):
    def setUp(self):
        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource)
        signals.connect_notify_ad_group_source_settings_change()

    @patch("automation.campaignstop.service.update_notifier.notify_ad_group_source_settings_change")
    def test_notify_ad_group_settings_change(self, mock_notify):
        changes = {"state": 1}
        self.ad_group_source.settings.update(None, skip_automation=True, **changes)
        mock_notify.assert_called_with(self.ad_group_source.settings, changes)
