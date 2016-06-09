from django.test import TestCase
import dash.models
import dash.history_helpers
import dash.constants
from zemauth.models import User


class HistoryHelperTests(TestCase):
    fixtures = ['test_api']

    def test_write_none(self):
        user = User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        dash.history_helpers.write_ad_group_history(
            ad_group,
            '',
            user=user,
            history_type=dash.constants.AdGroupHistoryType.AD_GROUP
        )
        self.assertEqual(0, dash.models.AdGroupHistory.objects.all().count())

        campaign = ad_group.campaign
        dash.history_helpers.write_campaign_history(
            campaign,
            None,
            user=user,
            history_type=dash.constants.CampaignHistoryType.CAMPAIGN
        )
        self.assertEqual(0, dash.models.CampaignHistory.objects.all().count())

        account = campaign.account
        dash.history_helpers.write_account_history(
            account,
            '',
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
            history_type=dash.constants.AccountHistoryType.ACCOUNT
        )
        self.assertEqual(0, dash.models.AccountHistory.objects.all().count())

    def test_write_ad_group(self):
        user = User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        dash.history_helpers.write_ad_group_history(
            ad_group,
            'Funky test',
            user=user,
            history_type=dash.constants.AdGroupHistoryType.AD_GROUP
        )

        hist = dash.models.AdGroupHistory.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(ad_group, hist.ad_group)
        self.assertEqual(dash.constants.AdGroupHistoryType.AD_GROUP, hist.type)
        self.assertEqual(user, hist.created_by)
        self.assertEqual('Funky test', hist.changes_text)

    def test_write_campaign(self):
        user = User.objects.get(pk=1)
        campaign= dash.models.Campaign.objects.get(pk=1)
        dash.history_helpers.write_campaign_history(
            campaign,
            'Funky test',
            user=user,
            history_type=dash.constants.CampaignHistoryType.CAMPAIGN
        )

        hist = dash.models.CampaignHistory.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(campaign, hist.campaign)
        self.assertEqual(dash.constants.CampaignHistoryType.CAMPAIGN, hist.type)
        self.assertEqual(user, hist.created_by)
        self.assertEqual('Funky test', hist.changes_text)

    def test_write_account(self):
        account = dash.models.Account.objects.get(pk=1)
        dash.history_helpers.write_account_history(
            account,
            'Funky test',
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
            history_type=dash.constants.AccountHistoryType.ACCOUNT
        )

        hist = dash.models.AccountHistory.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(account, hist.account)
        self.assertEqual(dash.constants.AccountHistoryType.ACCOUNT, hist.type)
        self.assertIsNone(hist.created_by)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, hist.system_user)
        self.assertEqual('Funky test', hist.changes_text)
