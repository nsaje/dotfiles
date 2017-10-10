import datetime
import decimal
from mock import patch

from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity
import core.goals
import core.bcm


class CampaignBcmMixin(TestCase):

    def setUp(self):
        self.agency = magic_mixer.blend(core.entity.Agency)
        self.account = magic_mixer.blend(core.entity.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)

    def test_get_todays_fee_and_margin(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        magic_mixer.blend(core.bcm.CreditLineItem,
                          account=self.account,
                          start_date=yesterday,
                          end_date=today,
                          status=constants.CreditLineItemStatus.SIGNED,
                          amount=decimal.Decimal('1000.0'),
                          flat_fee_cc=0,
                          license_fee=decimal.Decimal('0.2121'))

        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   account=self.account,
                                   start_date=yesterday,
                                   end_date=today,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.3333'))

        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=self.campaign,
                          start_date=yesterday,
                          end_date=today,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.2200'))

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal('0.3333'))
        self.assertEqual(margin, decimal.Decimal('0.2200'))

    def test_get_todays_fee_and_margin_nothing(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   account=self.account,
                                   start_date=yesterday,
                                   end_date=yesterday,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.2121'))

        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=self.campaign,
                          start_date=yesterday,
                          end_date=yesterday,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.2200'))

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, None)
        self.assertEqual(margin, None)


class MigrateToBCMV2Test(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign)
        self.campaign_goal = magic_mixer.blend(core.goals.CampaignGoal, campaign=self.campaign)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)

    @patch('core.entity.Campaign.get_todays_fee_and_margin')
    @patch('core.entity.AdGroup.migrate_to_bcm_v2')
    @patch('core.goals.CampaignGoal.migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2(self, mock_ad_group_migrate, mock_campaign_goal_migrate, mock_get_fee_and_margin):
        mock_get_fee_and_margin.return_value = decimal.Decimal('0.2'), decimal.Decimal('0.1')

        request = magic_mixer.blend_request_user()
        self.campaign.migrate_to_bcm_v2(request)

        self.assertTrue(self.ad_group.migrate_to_bcm_v2.called)
        self.assertTrue(self.campaign_goal.migrate_to_bcm_v2.called)
