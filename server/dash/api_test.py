import decimal
import datetime

from django.test import TestCase

from dash import models


class AdGroupSettingsOrderTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_settings_changes(self):

        set1 = models.AdGroupSettings(
            created_dt=datetime.date.today(),

            state=1,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.1'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        set2 = models.AdGroupSettings(
            created_dt=datetime.date.today() - datetime.timedelta(days=1),

            state=2,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.2'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        self.assertEqual(set1.get_setting_changes(set1), {})

        self.assertEqual(
            set1.get_setting_changes(set2),
            {'state': 2, 'cpc_cc': decimal.Decimal('0.2')},
        )
