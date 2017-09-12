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
        ad_group.write_history(
            '',
            user=user,
        )
        self.assertEqual(0, dash.models.History.objects.all().count())

        campaign = ad_group.campaign
        campaign.write_history(
            None,
            user=user,
        )
        self.assertEqual(0, dash.models.History.objects.all().count())

        account = campaign.account
        account.write_history(
            '',
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
        )
        self.assertEqual(0, dash.models.History.objects.all().count())

    def test_write_ad_group(self):
        user = User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        ad_group.write_history(
            'Funky test',
            user=user,
        )

        hist = dash.models.History.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(ad_group, hist.ad_group)
        self.assertEqual(user, hist.created_by)
        self.assertEqual('Funky test', hist.changes_text)

    def test_write_campaign(self):
        user = User.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        campaign.write_history(
            'Funky test',
            user=user,
        )

        hist = dash.models.History.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(campaign, hist.campaign)
        self.assertEqual(user, hist.created_by)
        self.assertEqual('Funky test', hist.changes_text)

    def test_write_account(self):
        account = dash.models.Account.objects.get(pk=1)
        account.write_history(
            'Funky test',
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
        )

        hist = dash.models.History.objects.first()
        self.assertIsNotNone(hist)
        self.assertEqual(account, hist.account)
        self.assertIsNone(hist.created_by)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, hist.system_user)
        self.assertEqual('Funky test', hist.changes_text)
