import datetime

import mock
from django.test import TestCase

from analytics import monitor
from dash.models import BudgetDailyStatement
from dash.models import BudgetLineItem


def _create_daily_statement(date, budget, base_media_nano, base_data_nano=0, margin_nano=0):
    BudgetDailyStatement.objects.create(
        date=date,
        budget=budget,
        base_media_spend_nano=base_media_nano,
        base_data_spend_nano=base_data_nano,
        media_spend_nano=base_media_nano + budget.credit.service_fee / 2,
        data_spend_nano=base_data_nano + budget.credit.service_fee / 2,
        service_fee_nano=int(base_media_nano / (1 - budget.credit.service_fee)),
        license_fee_nano=int(base_media_nano / (1 - budget.credit.license_fee)),
        margin_nano=margin_nano,
    )


class AuditSpendPatternsTest(TestCase):
    fixtures = ["test_projections"]

    def setUp(self):
        _create_daily_statement(datetime.date(2015, 10, 29), BudgetLineItem.objects.get(pk=2), 900 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 10, 30), BudgetLineItem.objects.get(pk=2), 1000 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 10, 31), BudgetLineItem.objects.get(pk=2), 950 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 1), BudgetLineItem.objects.get(pk=2), 650 * 10 ** 9)

        _create_daily_statement(datetime.date(2015, 11, 19), BudgetLineItem.objects.get(pk=4), 900 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 20), BudgetLineItem.objects.get(pk=3), 900 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 21), BudgetLineItem.objects.get(pk=3), 1100 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 22), BudgetLineItem.objects.get(pk=3), 750 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 23), BudgetLineItem.objects.get(pk=3), 800 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 20), BudgetLineItem.objects.get(pk=5), 900 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 21), BudgetLineItem.objects.get(pk=5), 1100 * 10 ** 9)
        _create_daily_statement(datetime.date(2015, 11, 22), BudgetLineItem.objects.get(pk=5), 1000 * 10 ** 9)

    def test_audit_first_in_month(self):
        self.assertEqual(monitor.audit_spend_patterns(datetime.date(2015, 10, 31)), [])
        self.assertEqual(monitor.audit_spend_patterns(datetime.date(2015, 11, 1)), [])
        alarms = monitor.audit_spend_patterns(datetime.date(2015, 11, 1), first_in_month_threshold=0.9)
        self.assertTrue(alarms)
        self.assertEqual(alarms[0][0], datetime.date(2015, 11, 1))

    def test_audit_success(self):
        self.assertEqual(monitor.audit_spend_patterns(datetime.date(2015, 11, 22)), [])
        self.assertEqual(monitor.audit_spend_patterns(datetime.date(2015, 11, 21), day_range=2), [])
        self.assertEqual(monitor.audit_spend_patterns(datetime.date(2015, 11, 23), threshold=0.2), [])

    def test_audit_fail(self):
        alarms = monitor.audit_spend_patterns(datetime.date(2015, 11, 22), threshold=1.5)
        self.assertEqual(alarms[0][0], datetime.date(2015, 11, 22))
        alarms = monitor.audit_spend_patterns(datetime.date(2015, 11, 23))
        self.assertEqual(alarms[0][0], datetime.date(2015, 11, 23))


class AuditSpendIntegrity(TestCase):
    fixtures = ["test_projections"]

    def setUp(self):
        self.date = datetime.date(2015, 10, 29)
        _create_daily_statement(self.date, BudgetLineItem.objects.get(pk=2), 900 * 10 ** 9)

    @mock.patch("analytics.monitor._get_rs_spend")
    def test_audit_success(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            "base_media": 900000000000,
            "base_data": 0,
            "service_fee": 1000000000000,
            "license_fee": 1125000000000,
            "margin": 0,
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertFalse(alarms)

    @mock.patch("analytics.monitor._get_rs_spend")
    def test_audit_success_with_err(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            "base_media": 900000070000,
            "base_data": 0,
            "service_fee": 1000000000100,
            "license_fee": 1125000000300,
            "margin": 0,
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertFalse(alarms)

    @mock.patch("analytics.monitor._get_rs_spend")
    def test_audit_fail(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            "base_media": 900000000000,
            "base_data": 0,
            "service_fee": 1001100000000,
            "license_fee": 1145000000000,
            "margin": 0,
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertEqual(
            alarms,
            [
                (datetime.date(2015, 10, 29), "mv_adgroup_placement", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_placement", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_campaign_placement", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_campaign_placement", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_account_placement", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_account_placement", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_master", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_master", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_contentad", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_contentad", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_contentad_device", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_contentad_device", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_contentad_environment", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_contentad_environment", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_contentad_geo", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_contentad_geo", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_adgroup", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_adgroup", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_device", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_device", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_environment", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_environment", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_geo", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_adgroup_geo", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_campaign", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_campaign", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_campaign_device", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_campaign_device", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_campaign_environment", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_campaign_environment", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_campaign_geo", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_campaign_geo", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_account", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_account", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_account_device", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_account_device", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_account_environment", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_account_environment", "license_fee", -20000000000),
                (datetime.date(2015, 10, 29), "mv_account_geo", "service_fee", -1100000000),
                (datetime.date(2015, 10, 29), "mv_account_geo", "license_fee", -20000000000),
            ],
        )
