import decimal
import datetime

from django.test import TestCase

from dash import models
from dash import api


class UpdateAdGroupSourceState(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_should_update_if_changed(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_not_update_if_unchanged(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': latest_state.state,
            'cpc_cc': int(latest_state.cpc_cc * 10000),
            'daily_budget_cc': int(latest_state.daily_budget_cc * 10000)
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.id, latest_state.id)

    def test_should_update_if_no_state_yet(self):
        self.assertTrue(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).delete()

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

        self.assertEqual(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count(),
            1
        )

    def test_should_not_update_if_not_latest_settings(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf, settings_id=1)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.id, latest_state.id)

    def test_should_update_if_latest_settings(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf, settings_id=2)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_disregard_null_and_unspecified_fields(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': None,
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(new_latest_state.cpc_cc, latest_state.cpc_cc)
        self.assertEqual(new_latest_state.daily_budget_cc, latest_state.daily_budget_cc)


class AdGroupSourceSettingsWriterTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)
        self.writer = api.AdGroupSourceSettingsWriter(self.ad_group_source)
        self.ad_group_settings = \
            models.AdGroupSettings.objects \
                .filter(ad_group=self.ad_group_source.ad_group) \
                .latest('created_dt')
        assert self.ad_group_settings.state == 2

    def test_can_not_trigger_action_if_ad_group_disabled(self):
        self.assertFalse(self.writer.can_trigger_action())

    def test_can_trigger_action_if_ad_group_enabled(self):
        self.ad_group_settings.state = 1
        self.ad_group_settings.save()
        self.assertTrue(self.writer.can_trigger_action())

    def test_should_write_if_no_settings_yet(self):
        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # delete all ad_group_source_settings
        models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).delete()

        self.writer.set_state(1)

        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )

        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.state, 1)
        self.assertTrue(latest_settings.cpc_cc is None)
        self.assertTrue(latest_settings.daily_budget_cc is None)

    def test_should_write_if_changed(self):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.writer.set_cpc_cc(0.1)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

    def test_should_not_write_if_unchanged(self):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.writer.set_daily_budget_cc(50)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.id, new_latest_settings.id)
        self.assertEqual(latest_settings.state, new_latest_settings.state)
        self.assertEqual(latest_settings.cpc_cc, new_latest_settings.cpc_cc)
        self.assertEqual(latest_settings.daily_budget_cc, new_latest_settings.daily_budget_cc)



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
