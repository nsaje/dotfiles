import datetime
import decimal
from mock import patch, MagicMock

from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity
import core.bcm


class AdGroupBcmMixin(TestCase):

    def setUp(self):
        self.agency = magic_mixer.blend(core.entity.Agency)
        self.account = magic_mixer.blend(core.entity.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)

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

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal('0.3333'))
        self.assertEqual(margin, decimal.Decimal('0.2200'))

    def test_get_todays_fee_and_margin_no_budget(self):
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

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal('0.2121'))
        self.assertEqual(margin, None)

    def test_get_todays_fee_and_margin_agency_credit(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   agency=self.agency,
                                   start_date=yesterday,
                                   end_date=today,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.2121'))

        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=self.campaign,
                          start_date=yesterday,
                          end_date=today,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.2200'))

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal('0.2121'))
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

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, None)
        self.assertEqual(margin, None)


class MigrateToBcmV2Test(TestCase):

    def setUp(self):
        today = datetime.date.today()

        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   account=account,
                                   start_date=today,
                                   end_date=today,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.2'))

        campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=campaign,
                          start_date=today,
                          end_date=today,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.1'))

        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)

    @patch('utils.redirector_helper.insert_adgroup', MagicMock())
    @patch('utils.k1_helper.update_ad_group', MagicMock())
    @patch.object(core.entity.AdGroupSource, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2(self, mock_ad_group_source_migrate):
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group)

        self._test_migrate_to_bcm_v2()
        self.assertTrue(ad_group_source.migrate_to_bcm_v2.called)

    @patch('utils.redirector_helper.insert_adgroup', MagicMock())
    @patch('utils.k1_helper.update_ad_group', MagicMock())
    @patch.object(core.entity.AdGroupSource, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2_b1_sources_group_enabled(self, mock_ad_group_source_migrate):
        source_type = magic_mixer.blend(core.source.SourceType, type=constants.SourceType.B1)
        source = magic_mixer.blend(core.source.Source, source_type=source_type)
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=source)

        self._test_migrate_to_bcm_v2()
        self.assertFalse(ad_group_source.migrate_to_bcm_v2.called)

    def _test_migrate_to_bcm_v2(self):
        request = magic_mixer.blend_request_user(permissions=['can_set_ad_group_max_cpm'])
        self.ad_group.settings.update(
            request,
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
            b1_sources_group_daily_budget=decimal.Decimal('50'),
            b1_sources_group_cpc_cc=decimal.Decimal('0.3'),
            autopilot_daily_budget=decimal.Decimal('100'),
            max_cpm=decimal.Decimal('1.22'),
        )

        self.ad_group.migrate_to_bcm_v2(request)

        self.assertEqual(69, self.ad_group.settings.b1_sources_group_daily_budget)
        self.assertEqual(138, self.ad_group.settings.autopilot_daily_budget)
        self.assertEqual(decimal.Decimal('0.4167'), self.ad_group.settings.b1_sources_group_cpc_cc)
        self.assertEqual(decimal.Decimal('1.6944'), self.ad_group.settings.max_cpm)
