import backtosql
import datetime

from django.test import TestCase

import dash.constants

from etl import helpers
from etl.tests.test_materialize_views import TPConversionResults


class HelpersTest(TestCase, backtosql.TestSQLMixin):

    def test_get_local_date_context(self):
        context = helpers.get_local_date_context(datetime.date(2016, 5, 1))

        self.assertDictEqual(context, {
            'date': '2016-05-01',
            'tzdate_from': '2016-05-01',
            'tzhour_from': 4,
            'tzdate_to': '2016-05-02',
            'tzhour_to': 4,
        })

    def test_get_local_multiday_date_context_one_day(self):
        context = helpers.get_local_multiday_date_context(datetime.date(2016, 5, 1), datetime.date(2016, 5, 1))

        self.assertDictEqual(context, {
            'date_from': '2016-05-01',
            'date_to': '2016-05-01',
            'tzdate_from': '2016-05-01',
            'tzhour_from': 4,
            'tzdate_to': '2016-05-02',
            'tzhour_to': 4,
            'date_ranges': [{
                'date': '2016-05-01',
                'tzdate_from': '2016-05-01',
                'tzhour_from': 4,
                'tzdate_to': '2016-05-02',
                'tzhour_to': 4,
            }]
        })

    def test_get_local_multiday_date_context(self):
        context = helpers.get_local_multiday_date_context(datetime.date(2016, 5, 1), datetime.date(2016, 5, 3))

        self.assertDictEqual(context, {
            'date_from': '2016-05-01',
            'date_to': '2016-05-03',
            'tzdate_from': '2016-05-01',
            'tzhour_from': 4,
            'tzdate_to': '2016-05-04',
            'tzhour_to': 4,
            'date_ranges': [{
                'date': '2016-05-01',
                'tzdate_from': '2016-05-01',
                'tzhour_from': 4,
                'tzdate_to': '2016-05-02',
                'tzhour_to': 4,
            }, {
                'date': '2016-05-02',
                'tzdate_from': '2016-05-02',
                'tzhour_from': 4,
                'tzdate_to': '2016-05-03',
                'tzhour_to': 4,
            }, {
                'date': '2016-05-03',
                'tzdate_from': '2016-05-03',
                'tzhour_from': 4,
                'tzdate_to': '2016-05-04',
                'tzhour_to': 4,
            }]
        })

    def test_get_local_date_query(self):
        query = helpers.get_local_date_query(datetime.date(2016, 5, 1))

        self.assertSQLEquals(query, """\
        (date = '2016-05-01' and hour is null) or (
            hour is not null and (
                (date = '2016-05-01' and hour >= 4) or
                (date = '2016-05-02' and hour < 4)
            )
        )""")

    def test_calculate_effective_cost(self):
        factors = (0.2, 0.1)

        effective_cost, effective_data_cost, license_fee = helpers.calculate_effective_cost(250, 300, factors)

        self.assertEqual(effective_cost, 50.0)
        self.assertEqual(effective_data_cost, 60.0)
        self.assertEqual(license_fee, 11.0)

    def test_extract_source_slug(self):
        self.assertEqual(helpers.extract_source_slug('b1_outbrain'), 'outbrain')
        self.assertEqual(helpers.extract_source_slug('outbrain'), 'outbrain')

    def test_extract_device_type(self):
        self.assertEqual(helpers.extract_device_type(1), dash.constants.DeviceType.MOBILE)
        self.assertEqual(helpers.extract_device_type(2), dash.constants.DeviceType.DESKTOP)
        self.assertEqual(helpers.extract_device_type(5), dash.constants.DeviceType.TABLET)

        self.assertEqual(helpers.extract_device_type(None), dash.constants.DeviceType.UNDEFINED)
        self.assertEqual(helpers.extract_device_type(0), dash.constants.DeviceType.UNDEFINED)
        self.assertEqual(helpers.extract_device_type(3), dash.constants.DeviceType.UNDEFINED)

    def test_extract_age(self):
        self.assertEqual(helpers.extract_age('18-20'), dash.constants.AgeGroup.AGE_18_20)
        self.assertEqual(helpers.extract_age('21-29'), dash.constants.AgeGroup.AGE_21_29)
        self.assertEqual(helpers.extract_age('30-39'), dash.constants.AgeGroup.AGE_30_39)
        self.assertEqual(helpers.extract_age('40-49'), dash.constants.AgeGroup.AGE_40_49)
        self.assertEqual(helpers.extract_age('50-64'), dash.constants.AgeGroup.AGE_50_64)
        self.assertEqual(helpers.extract_age('65+'), dash.constants.AgeGroup.AGE_65_MORE)

        self.assertEqual(helpers.extract_age('Lol'), dash.constants.AgeGroup.UNDEFINED)

    def test_extract_gender(self):
        self.assertEqual(helpers.extract_gender('male'), dash.constants.Gender.MEN)
        self.assertEqual(helpers.extract_gender('female'), dash.constants.Gender.WOMEN)
        self.assertEqual(helpers.extract_gender('nesto'), dash.constants.Gender.UNDEFINED)

    def test_extract_age_gender(self):
        self.assertEqual(helpers.extract_age_gender(dash.constants.AgeGroup.AGE_50_64, dash.constants.Gender.WOMEN),
                         dash.constants.AgeGenderGroup.AGE_50_64_WOMEN)
        self.assertEqual(helpers.extract_age_gender(dash.constants.AgeGroup.AGE_21_29, dash.constants.Gender.UNDEFINED),
                         dash.constants.AgeGenderGroup.AGE_21_29_UNDEFINED)
        self.assertEqual(helpers.extract_age_gender(dash.constants.AgeGroup.UNDEFINED, dash.constants.Gender.WOMEN),
                         dash.constants.AgeGenderGroup.UNDEFINED)

    def test_extract_postclick_source(self):
        self.assertEqual(helpers.extract_postclick_source('gaapi'), 'gaapi')
        self.assertEqual(helpers.extract_postclick_source('ga_mail'), 'ga_mail')
        self.assertEqual(helpers.extract_postclick_source('omniture'), 'omniture')
        self.assertEqual(helpers.extract_postclick_source('lol'), 'other')

    def test_get_highest_priority_postclick_source(self):
        self.assertEqual(helpers.get_highest_priority_postclick_source({
            'gaapi': 1,
            'ga_mail': 2,
        }), 1)
        self.assertEqual(helpers.get_highest_priority_postclick_source({
            'ga_mail': 2,
        }), 2)
        self.assertEqual(helpers.get_highest_priority_postclick_source({
            'ga_mail': 2,
            'omniture': 3,
            'other': 4,
        }), 2)
        self.assertEqual(helpers.get_highest_priority_postclick_source({
            'omniture': 3,
            'other': 4,
        }), 3)
        self.assertEqual(helpers.get_highest_priority_postclick_source({
            'other': 4,
        }), 4)
