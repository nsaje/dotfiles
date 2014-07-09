import datetime
from decimal import Decimal

from django.test import TestCase

from dash import models


class AdGroupSettingsTest(TestCase):

    fixtures = ['test_models.yaml']

    def test_settings_fields(self):
        meta_fields = [
            'id',
            'ad_group',
            'ad_group_id',
            'created_dt',
            'created_by',
            'created_by_id',
        ]

        all_fields = set(models.AdGroupSettings._settings_fields + meta_fields)
        model_fields = set(models.AdGroupSettings._meta.get_all_field_names())

        self.assertEqual(model_fields, all_fields)

    def test_get_settings_dict(self):
        settings_dict = {
            'state': 1,
            'cpc_cc': Decimal('0.12'),
            'daily_budget_cc': Decimal('50'),
            'start_date': datetime.date(2014, 6, 4),
            'end_date': datetime.date(2014, 6, 5),
            'target_devices': u'',
            'tracking_code': u'',
            'target_regions': u'',
        }
        self.assertEqual(
            models.AdGroupSettings.objects.get(id=1).get_settings_dict(),
            settings_dict,
        )
