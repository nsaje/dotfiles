import decimal

from django.test import TestCase

import core.entity
import core.source
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper, exc

from . import validation


class ValidateAdGroupSourceUpdatesTestCase(TestCase):

    def setUp(self):
        today = dates_helper.local_today()
        self.account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=True)
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.account,
            start_date=dates_helper.day_before(today),
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal('1000.0'),
            flat_fee_cc=0,
            license_fee=decimal.Decimal('0.15')
        )

        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.day_before(today),
            end_date=today,
            credit=self.credit,
            amount=decimal.Decimal('200'),
            margin=decimal.Decimal('0.30')
        )

        source_type = magic_mixer.blend(
            core.source.SourceType,
            min_cpc=decimal.Decimal('0.03'),
            min_daily_budget=decimal.Decimal('10'),
            max_cpc=decimal.Decimal('5'),
            max_daily_budget=decimal.Decimal('10000'),
        )
        self.source = magic_mixer.blend(core.source.Source, source_type=source_type)

    def test_validate_ad_group_source_cpc_cc(self):
        ad_group_source = magic_mixer.blend(
            core.entity.AdGroupSource, ad_group__campaign=self.campaign, source=self.source)
        ad_group_source.settings.update(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpc_cc=decimal.Decimal('0.35'),
            daily_budget_cc=decimal.Decimal('50')
        )

        updates = {}
        updates['cpc_cc'] = decimal.Decimal('0.05')
        with self.assertRaises(exc.ValidationError) as cm:
            validation.validate_ad_group_source_updates(
                ad_group_source,
                updates,
                ad_group_source.ad_group.get_current_settings(),
                ad_group_source.settings,
            )

        exception = cm.exception
        self.assertEqual(1, len(exception.errors['cpc_cc']))
        self.assertTrue('$0.051' in exception.errors['cpc_cc'][0])

        updates['cpc_cc'] = decimal.Decimal('8.404')
        with self.assertRaises(exc.ValidationError) as cm:
            validation.validate_ad_group_source_updates(
                ad_group_source,
                updates,
                ad_group_source.ad_group.get_current_settings(),
                ad_group_source.settings,
            )

        exception = cm.exception
        self.assertEqual(1, len(exception.errors['cpc_cc']))
        self.assertTrue('$8.403' in exception.errors['cpc_cc'][0])

        updates['cpc_cc'] = decimal.Decimal('5')
        validation.validate_ad_group_source_updates(
            ad_group_source,
            updates,
            ad_group_source.ad_group.get_current_settings(),
            ad_group_source.settings,
        )

    def test_validate_ad_group_source_daily_budget(self):
        ad_group_source = magic_mixer.blend(
            core.entity.AdGroupSource, ad_group__campaign=self.campaign, source=self.source)
        ad_group_source.settings.update(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpc_cc=decimal.Decimal('0.35'),
            daily_budget_cc=decimal.Decimal('50')
        )

        updates = {}
        updates['daily_budget_cc'] = decimal.Decimal('0.5')
        with self.assertRaises(exc.ValidationError) as cm:
            validation.validate_ad_group_source_updates(
                ad_group_source,
                updates,
                ad_group_source.ad_group.get_current_settings(),
                ad_group_source.settings,
            )

        exception = cm.exception
        self.assertEqual(1, len(exception.errors['daily_budget_cc']))
        self.assertTrue('$17' in exception.errors['daily_budget_cc'][0])

        updates['daily_budget_cc'] = decimal.Decimal('99999')
        with self.assertRaises(exc.ValidationError) as cm:
            validation.validate_ad_group_source_updates(
                ad_group_source,
                updates,
                ad_group_source.ad_group.get_current_settings(),
                ad_group_source.settings,
            )

        exception = cm.exception
        self.assertEqual(1, len(exception.errors['daily_budget_cc']))
        self.assertTrue('$16806' in exception.errors['daily_budget_cc'][0])

        updates['daily_budget_cc'] = decimal.Decimal('100')
        validation.validate_ad_group_source_updates(
            ad_group_source,
            updates,
            ad_group_source.ad_group.get_current_settings(),
            ad_group_source.settings,
        )
