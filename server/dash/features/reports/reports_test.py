import datetime
from decimal import Decimal

import mock
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings

import core.models
import dash.constants
import utils.dates_helper
import utils.test_helper
from dash.features import geolocation
from dash.features import scheduled_reports
from utils import dates_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import constants
from . import reports
from .reportjob import ReportJob
from .reports import ReportJobExecutor

TEST_FTP_CONFIG_1 = {"ftp_server": "127.0.0.1", "ftp_port": 21, "ftp_user": "test1", "ftp_password": "test2"}
TEST_FTP_CONFIG_2 = {"ftp_server": "127.0.0.1", "ftp_port": 2121, "ftp_user": "test2", "ftp_password": "test2"}
TEST_FTP_REPORTS = {
    # Key is the report ID, Value is the remote destination for that report
    1: {"destination": "account1", "config": TEST_FTP_CONFIG_1},
    2: {"destination": "account2", "server_config": TEST_FTP_CONFIG_1},
    3: {"destination": "account3", "config": TEST_FTP_CONFIG_1},
    4: {"destination": "account4", "config": TEST_FTP_CONFIG_1},
    5: {"destination": "account5", "config": TEST_FTP_CONFIG_1},
    6: {"destination": "", "config": TEST_FTP_CONFIG_2},
}


class ReportsExecuteTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = self.user
        self.reportJob.save()

        influx_incr_patcher = mock.patch("utils.metrics_compat.incr")
        self.mock_influx_incr = influx_incr_patcher.start()
        self.addCleanup(influx_incr_patcher.stop)

    def assertJobFailed(self, status, result, exception=None):
        self.mock_influx_incr.assert_called_once_with("dash.reports", 1, status=status)

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual(result, self.reportJob.result)
        if exception is not None:
            self.assertIn(str(exception), self.reportJob.exception)

    @mock.patch("dash.features.reports.reports._send_fail_mail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_handle_exception(self, mock_get_report, mock_send_fail):
        e = Exception("test-error")
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with(self.reportJob)
        self.assertJobFailed(
            "failed", "Internal Error: Please contact support. Report job ID is %d." % self.reportJob.id, e
        )

    @mock.patch("dash.features.reports.reports._send_fail_mail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_handle_soft_time_limit(self, mock_get_report, mock_send_fail):
        e = SoftTimeLimitExceeded()
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with(self.reportJob)
        self.assertJobFailed(
            "timeout", "Job Timeout: Requested report probably too large. Report job ID is %d." % self.reportJob.id
        )

    @mock.patch("utils.dates_helper.utc_now")
    @mock.patch("dash.features.reports.reports._send_fail_mail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_too_old(self, mock_get_report, mock_send_fail, mock_now):
        mock_get_report.side_effect = Exception("test-error")
        mock_now.return_value = datetime.datetime(2017, 8, 1, 11, 31)

        self.reportJob.created_dt = datetime.datetime(2017, 8, 1, 10, 30)
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()
        mock_send_fail.assert_called_once_with(self.reportJob)
        self.assertJobFailed("too_old", "Service Timeout: Please try again later.")

    @mock.patch("utils.dates_helper.utc_now")
    @mock.patch("dash.features.reports.reports._send_fail_mail")
    def test_clean_old_in_progress(self, mock_send_fail, mock_now):
        mock_now.return_value = datetime.datetime(2017, 8, 1, 11, 31)

        self.reportJob.created_dt = datetime.datetime(2017, 8, 1, 10, 30)
        self.reportJob.status = constants.ReportJobStatus.IN_PROGRESS
        self.reportJob.save()

        created_before = dates_helper.utc_now() - datetime.timedelta(minutes=30)
        cleaned_up_count = reports.clean_up_old_in_progress_reports(created_before)

        self.assertEqual(1, cleaned_up_count)
        mock_send_fail.assert_called_once_with(self.reportJob)
        self.assertJobFailed(
            "stale",
            "Job Timeout: Requested report is taking too long to complete. Report job ID is %d." % self.reportJob.id,
        )

    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_incorrect_state(self, mock_get_report):
        mock_get_report.side_effect = Exception("test-error")

        self.reportJob.status = constants.ReportJobStatus.DONE
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()

    @mock.patch("utils.email_helper.send_async_report_fail")
    def test_send_fail(self, mock_send):
        account = self.mix_account(self.reportJob.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        self.reportJob.query = {
            "options": {
                "recipients": ["test@test.com"],
                "show_archived": False,
                "show_blacklisted_publishers": False,
                "include_totals": False,
            },
            "filters": [
                {"field": "Date", "operator": "between", "from": "2017-08-01", "to": "2017-08-01"},
                {"field": "Ad Group Id", "operator": "=", "value": str(ad_group.id)},
            ],
            "fields": [{"field": "Content Ad"}, {"field": "Clicks"}],
        }

        reports._send_fail_mail(self.reportJob)

        mock_send.assert_called_once_with(
            user=self.reportJob.user,
            recipients=["test@test.com"],
            start_date=datetime.date(2017, 8, 1),
            end_date=datetime.date(2017, 8, 1),
            columns=["Content Ad", "Clicks"],
            filtered_sources=[],
            show_archived=False,
            show_blacklisted_publishers=False,
            view="Content Ad",
            breakdowns=[],
            include_totals=False,
            ad_group_name=ad_group.name,
            campaign_name=ad_group.campaign.name,
            account_name=ad_group.campaign.account.name,
        )

    @mock.patch("utils.email_helper.send_async_report_fail")
    def test_send_fail_scheduled_report(self, mock_send):
        self.reportJob.query = {"options": {"recipients": ["test@test.com"]}}
        self.reportJob.scheduled_report = scheduled_reports.models.ScheduledReport()

        reports._send_fail_mail(self.reportJob)

        mock_send.assert_not_called()

    @mock.patch("dash.features.reports.reports.ReportJobExecutor.send_by_email")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.save_to_s3")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_success(self, mock_get_report, mock_save, mock_send):
        mock_get_report.return_value = (1, 2)
        mock_save.return_value = "test-report-path"

        reports.execute(self.reportJob.id)

        self.mock_influx_incr.assert_called_once_with("dash.reports", 1, status="success")

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.DONE, self.reportJob.status)
        self.assertEqual("test-report-path", self.reportJob.result)

    @mock.patch("dash.features.reports.reports.ReportJobExecutor.send_by_email")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.save_to_ftp")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.save_to_s3")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    @mock.patch("django.conf.settings.FTP_REPORTS", TEST_FTP_REPORTS)
    def test_ftp_success(self, mock_get_report, mock_save, mock_ftp, mock_send):
        self.reportJob.scheduled_report = magic_mixer.blend(
            scheduled_reports.ScheduledReport, id=list(settings.FTP_REPORTS.keys())[0], query={}
        )
        self.reportJob.save()
        mock_get_report.return_value = ("a_csv_report", "report_file_name")
        mock_save.return_value = "test-report-path"
        reports.execute(self.reportJob.id)
        ftp_report = settings.FTP_REPORTS[self.reportJob.scheduled_report.id]
        mock_ftp.assert_called_with(
            ftp_report["config"].get("ftp_server"),
            ftp_report["config"].get("ftp_port"),
            ftp_report["config"].get("ftp_user"),
            ftp_report["config"].get("ftp_password"),
            ftp_report["destination"],
            "{}-{}.csv".format(
                ftp_report["destination"], datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
            ),
            "a_csv_report",
        )

        self.mock_influx_incr.assert_called_once_with("dash.reports", 1, status="success")

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.DONE, self.reportJob.status)
        self.assertEqual("test-report-path", self.reportJob.result)

    @mock.patch("dash.features.reports.reports.ReportJobExecutor.send_by_email")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.save_to_ftp")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.save_to_s3")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    @mock.patch("django.conf.settings.FTP_REPORTS", TEST_FTP_REPORTS)
    def test_ftp_fail(self, mock_get_report, mock_save, mock_ftp, mock_send):
        self.reportJob.scheduled_report = magic_mixer.blend(
            scheduled_reports.ScheduledReport, id=list(settings.FTP_REPORTS.keys())[0], query={}
        )
        self.reportJob.save()
        mock_get_report.return_value = ("a_csv_report", "report_file_name")
        mock_save.return_value = "test-report-path"
        mock_ftp.side_effect = ConnectionError("connection failed")

        reports.execute(self.reportJob.id)
        ftp_report = settings.FTP_REPORTS[self.reportJob.scheduled_report.id]
        mock_ftp.assert_called_with(
            ftp_report["config"].get("ftp_server"),
            ftp_report["config"].get("ftp_port"),
            ftp_report["config"].get("ftp_user"),
            ftp_report["config"].get("ftp_password"),
            ftp_report["destination"],
            "{}-{}.csv".format(
                ftp_report["destination"], datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
            ),
            "a_csv_report",
        )
        self.mock_influx_incr.assert_called_once_with("dash.reports", 1, status="failed")
        self.reportJob.refresh_from_db()
        self.assertNotEqual(constants.ReportJobStatus.DONE, self.reportJob.status)
        self.assertNotEqual("test-report-path", self.reportJob.result)

    def test_get_csv_separator(self):
        self.mix_agency(
            self.reportJob.user,
            permissions=[Permission.READ, Permission.WRITE],
            default_csv_decimal_separator=",",
            default_csv_separator=";",
        )

        self.reportJob.query = {}
        self.reportJob.query["options"] = {}
        self.assertEqual(ReportJobExecutor._get_csv_separators(self.reportJob), (";", ","))

        self.reportJob.query["options"]["csv_separator"] = "\t"
        self.reportJob.query["options"]["csv_decimal_separator"] = "."
        self.assertEqual(ReportJobExecutor._get_csv_separators(self.reportJob), ("\t", "."))


class ReportsGetReportCSVTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = self.user
        self.reportJob.save()

        influx_incr_patcher = mock.patch("utils.metrics_compat.incr")
        self.mock_influx_incr = influx_incr_patcher.start()
        self.addCleanup(influx_incr_patcher.stop)

    @staticmethod
    def build_query(
        fields=[],
        filters=[],
        include_totals=False,
        all_accounts_in_local_currency=False,
        csv_separator=None,
        csv_decimal_separator=None,
        show_status_date=False,
    ):
        return {
            "fields": [{"field": field} for field in fields],
            "filters": [{"field": "Date", "operator": "=", "value": "2019-02-13"}] + filters,
            "options": {
                "show_archived": False,
                "show_blacklisted_publishers": False,
                "recipients": [],
                "include_items_with_no_spend": False,
                "show_status_date": show_status_date,
                "include_totals": include_totals,
                "all_accounts_in_local_currency": all_accounts_in_local_currency,
                "csv_separator": csv_separator,
                "csv_decimal_separator": csv_decimal_separator,
            },
        }

    @mock.patch("stats.api_reports.query")
    def test_basic(self, mock_query):
        self.reportJob.query = self.build_query(["Ad Group Id", "Total Spend", "Clicks"])
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id","Total Spend","Clicks","Currency"\r\n"1","12.3000","5","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.totals")
    @mock.patch("stats.api_reports.query")
    def test_include_totals(self, mock_query, mock_totals):
        self.reportJob.query = self.build_query(["Ad Group Id", "Total Spend", "Clicks"], include_totals=True)
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        mock_totals.return_value = row
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id","Total Spend","Clicks","Currency"\r\n"1","12.3000","5","USD"\r\n"1","12.3000","5","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_no_cost_fields_no_currency(self, mock_query):
        self.reportJob.query = self.build_query(["Ad Group Id", "Clicks"])
        row = {"ad_group_id": 1, "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id","Clicks"\r\n"1","5"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_dated_columns(self, mock_query):
        self.reportJob.query = self.build_query(
            ["Ad Group Id", "Total Spend", "Clicks", "Status"], show_status_date=True
        )
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5, "status": "ACTIVE"}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        today = dates_helper.local_today()
        expected = """"Ad Group Id","Total Spend","Clicks","Status ({})","Currency"\r\n"1","12.3000","5","ACTIVE","USD"\r\n""".format(
            today.isoformat()
        )
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_currency(self, mock_query):
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__currency="EUR")
        self.reportJob.query = self.build_query(
            ["Ad Group Id", "Total Spend", "Clicks"],
            filters=[{"field": "Ad Group Id", "operator": "=", "value": ad_group.id}],
        )
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id","Total Spend","Clicks","Currency"\r\n"1","12.3000","5","EUR"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_all_accounts_in_local_currency(self, mock_query):
        self.reportJob.query = self.build_query(
            ["Account Id", "Total Spend", "Clicks"],
            filters=[{"field": "Account Id", "operator": "IN", "values": ["1", "2"]}],
            all_accounts_in_local_currency=True,
        )
        self.mix_account(self.reportJob.user, permissions=[Permission.READ, Permission.WRITE], currency="EUR", id=1)
        self.mix_account(self.reportJob.user, permissions=[Permission.READ, Permission.WRITE], currency="USD", id=2)
        mock_query.return_value = [
            {"account_id": 1, "etfm_cost": Decimal("12.3"), "local_etfm_cost": Decimal("15.4"), "clicks": 5},
            {"account_id": 2, "etfm_cost": Decimal("13.4"), "local_etfm_cost": Decimal("16.4"), "clicks": 8},
        ]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Account Id","Total Spend","Clicks","Currency"\r\n"1","15.4000","5","EUR"\r\n"2","16.4000","8","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_all_accounts_delivery_not_in_local_currency(self, mock_query):
        self.reportJob.query = self.build_query(
            ["Media Source Id", "Total Spend", "Clicks"],
            filters=[{"field": "Media Source Id", "operator": "IN", "values": ["1", "2"]}],
            all_accounts_in_local_currency=True,
        )
        mock_query.return_value = [
            {"source_id": 1, "etfm_cost": Decimal("12.3"), "local_etfm_cost": Decimal("15.4"), "clicks": 5},
            {"source_id": 2, "etfm_cost": Decimal("13.4"), "local_etfm_cost": Decimal("16.4"), "clicks": 8},
        ]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Media Source Id","Total Spend","Clicks","Currency"\r\n"1","12.3000","5","USD"\r\n"2","13.4000","8","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.totals")
    @mock.patch("stats.api_reports.query")
    def test_csv_config(self, mock_query, mock_totals):
        self.reportJob.query = self.build_query(
            ["Ad Group Id", "Total Spend", "Clicks"], include_totals=True, csv_separator=";", csv_decimal_separator=","
        )
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row.copy()]
        mock_totals.return_value = row.copy()
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id";"Total Spend";"Clicks";"Currency"\r\n"1";"12,3000";"5";"USD"\r\n"1";"12,3000";"5";"USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_device(self, mock_query):
        self.reportJob.query = self.build_query(["Device"])
        row = {"device_type": 4, "etfm_cost": Decimal("12.3"), "clicks": 5, "status": "ACTIVE"}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Device","Device Name"\r\n"MOBILE","Mobile"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_device_os(self, mock_query):
        self.reportJob.query = self.build_query(["Operating System"])
        row = {"device_os": "android", "etfm_cost": Decimal("12.3"), "clicks": 5, "status": "ACTIVE"}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Operating System","Operating System Name"\r\n"ANDROID","Android"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_state_region(self, mock_query):
        magic_mixer.blend(geolocation.Geolocation, key="IT-25", name="Lombardy, Italy")
        self.reportJob.query = self.build_query(["State / Region"])
        row = {"region": "IT-25", "etfm_cost": Decimal("12.3"), "clicks": 5, "status": "ACTIVE"}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"State / Region","State / Region Name"\r\n"IT-25","Lombardy, Italy"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_device_clicks_state_region(self, mock_query):
        magic_mixer.blend(geolocation.Geolocation, key="IT-25", name="Lombardy, Italy")
        self.reportJob.query = self.build_query(["Device", "Clicks", "State / Region"])
        row = {"device_type": 4, "region": "IT-25", "etfm_cost": Decimal("12.3"), "clicks": 5, "status": "ACTIVE"}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Device","Device Name","Clicks","State / Region","State / Region Name"\r\n"MOBILE","Mobile","5","IT-25","Lombardy, Italy"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_environment(self, mock_query):
        self.reportJob.query = self.build_query(["Environment"])
        row = {"environment": "app", "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Environment","Environment Name"\r\n"APP","In-app"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_placement(self, mock_query):
        self.reportJob.query = self.build_query(["Placement"])
        row = {"placement": "00000000-0029-e16a-0000-000000000071", "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Placement"\r\n"00000000-0029-e16a-0000-000000000071"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_placement_all_related_columns(self, mock_query):
        self.reportJob.query = self.build_query(
            [
                "Placement Id",
                "Placement",
                "Placement Type",
                "Publisher Id",
                "Publisher",
                "Link",
                "Source ID",
                "Media Source",
                "Source Slug",
                "Ad Group Id",
                "Status",
                "Blacklisted Level",
                "Publisher Status",
                "Clicks",
            ]
        )
        mock_query.return_value = [
            {
                "placement_id": "pubx.com__2__plac1",
                "publisher": "pubx.com",
                "placement": "plac1",
                "source_id": 2,
                "source_slug": "gravity",
                "domain_link": "http://pubx.com",
                "status": "ACTIVE",
                "blacklisted_level": "",
                "ad_group_id": 1,
                "clicks": 1,
                "publisher_id": "pubx.com__2",
                "publisher_status": "ACTIVE",
                "source": "Gravity",
                "placement_type": "In feed",
            }
        ]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Placement Id","Placement","Placement Type","Publisher Id","Publisher","Link","Source ID","Media Source","Source Slug","Ad Group Id","Status","Blacklisted Level","Publisher Status","Clicks"\r\n"pubx.com__2__plac1","plac1","In feed","pubx.com__2","pubx.com","http://pubx.com","2","Gravity","gravity","1","ACTIVE","","ACTIVE","1"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_browser(self, mock_query):
        self.reportJob.query = self.build_query(["Browser"])
        row = {"browser": "CHROME", "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Browser","Browser Name"\r\n"CHROME","Chrome"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_connection_type(self, mock_query):
        self.reportJob.query = self.build_query(["Connection Type"])
        row = {"connection_type": "wifi", "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Connection Type","Connection Type Name"\r\n"WIFI","Wi-Fi"\r\n"""
        self.assertEqual(expected, output)


class IncludeEntityTagsReportTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.agency = self.mix_agency(self.user, permissions=[Permission.WRITE, Permission.READ])
        self.agency.entity_tags.add("some/agency", "another/agency")

        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.account.entity_tags.add("some/account", "another/account")

        self.another_account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.another_account.entity_tags.add("other/account", "foreign/account")

        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.campaign.entity_tags.add("some/campaign", "another/campaign")

        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group.entity_tags.add("some/ad_group", "another/ad_group")

        self.source = magic_mixer.blend(core.models.Source)
        self.source.entity_tags.add("some/source", "another/source")

        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=self.source)
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = self.user
        self.reportJob.save()
        utils.test_helper.add_permissions(self.reportJob.user, ["can_include_tags_in_reports"])

        influx_incr_patcher = mock.patch("utils.metrics_compat.incr")
        self.mock_influx_incr = influx_incr_patcher.start()
        self.addCleanup(influx_incr_patcher.stop)

    @staticmethod
    def build_query(fields=[], include_entity_tags=None):
        return {
            "fields": [{"field": field} for field in fields],
            "filters": [{"field": "Date", "operator": "=", "value": "2019-02-13"}],
            "options": {
                "show_archived": False,
                "show_blacklisted_publishers": False,
                "recipients": [],
                "include_items_with_no_spend": False,
                "show_status_date": False,
                "include_totals": False,
                "all_accounts_in_local_currency": False,
                "csv_separator": None,
                "csv_decimal_separator": None,
                "include_entity_tags": include_entity_tags,
            },
        }

    @mock.patch("redshiftapi.api_reports.query")
    def test_all(self, mock_query):
        self.reportJob.query = self.build_query(
            ["Account Id", "Campaign Id", "Ad Group Id", "Media Source Id"], include_entity_tags=True
        )
        row = {
            "account_id": self.account.id,
            "campaign_id": self.campaign.id,
            "ad_group_id": self.ad_group.id,
            "source_id": self.source.id,
        }
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Account Id","Campaign Id","Ad Group Id","Media Source Id","Agency Tags","Account Tags","Campaign Tags","Ad Group Tags","Source Tags"\r\n"%s","%s","%s","%s","another/agency,some/agency","another/account,some/account","another/campaign,some/campaign","another/ad_group,some/ad_group","another/source,some/source"\r\n"""
            % (self.account.id, self.campaign.id, self.ad_group.id, self.source.id)
        )
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_account(self, mock_query):
        self.reportJob.query = self.build_query(["Account Id"], include_entity_tags=True)
        row = {"account_id": self.account.id}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Account Id","Agency Tags","Account Tags"\r\n"%s","another/agency,some/agency","another/account,some/account"\r\n"""
            % self.account.id
        )
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_account_without_agency(self, mock_query):
        self.reportJob.query = self.build_query(["Account Id"], include_entity_tags=True)

        row = {"account_id": self.another_account.id}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Account Id","Agency Tags","Account Tags"\r\n"%s","","foreign/account,other/account"\r\n"""
            % self.another_account.id
        )
        self.assertEqual(expected, output)

        mock_query.return_value = [{"account_id": self.account.id}, {"account_id": self.another_account.id}]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Account Id","Agency Tags","Account Tags"\r\n"%s","another/agency,some/agency","another/account,some/account"\r\n"%s","","foreign/account,other/account"\r\n"""
            % (self.account.id, self.another_account.id)
        )
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_campaign(self, mock_query):
        self.reportJob.query = self.build_query(["Campaign Id"], include_entity_tags=True)
        row = {"campaign_id": self.campaign.id}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Campaign Id","Agency Tags","Account Tags","Campaign Tags"\r\n"%s","another/agency,some/agency","another/account,some/account","another/campaign,some/campaign"\r\n"""
            % self.campaign.id
        )
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_ad_group(self, mock_query):
        self.reportJob.query = self.build_query(["Ad Group Id"], include_entity_tags=True)
        row = {"ad_group_id": self.ad_group.id}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = (
            """"Ad Group Id","Agency Tags","Account Tags","Campaign Tags","Ad Group Tags"\r\n"%s","another/agency,some/agency","another/account,some/account","another/campaign,some/campaign","another/ad_group,some/ad_group"\r\n"""
            % self.ad_group.id
        )
        self.assertEqual(expected, output)

    @mock.patch("redshiftapi.api_reports.query")
    def test_source(self, mock_query):
        self.reportJob.query = self.build_query(["Media Source Id"], include_entity_tags=True)
        row = {"source_id": self.source.id}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Media Source Id","Source Tags"\r\n"%s","another/source,some/source"\r\n""" % self.source.id
        self.assertEqual(expected, output)


class ReportsImplementationTestCase(BaseTestCase):
    def setUp(self):
        self.user = magic_mixer.blend_user()
        self.report_job = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.report_job.user = self.user
        self.report_job.save()

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_raw_new_report_no_options(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Publisher"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["publisher_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["publisher_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="ad_groups",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_raw_new_report_data_filters(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Account Id"}],
            "filters": [
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Account Type", "operator": "IN", "values": ["1"]},
                {"field": "Agency", "operator": "IN", "values": ["1"]},
                {"field": "Business", "operator": "IN", "values": ["z1", "oen"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["account_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=utils.test_helper.QuerySetMatcher(core.models.Agency.objects.filter(pk__in=[1])),
            filtered_account_types=[1],
            filtered_businesses=["z1", "oen"],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["account_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="all_accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_raw_new_report_batch(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        mock_query.side_effect = [[{}] * reports.BATCH_ROWS, [{}] * 100]
        query = {
            "fields": [{"field": "Publisher"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["publisher_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            ad_group_ids=[1],
        )

        mock_query.assert_has_calls(
            [
                mock.call(
                    user=self.user,
                    breakdown=["publisher_id"],
                    constraints=mock.ANY,
                    goals=mock.ANY,
                    order="-e_media_cost",
                    offset=0,
                    limit=reports.BATCH_ROWS,
                    level="ad_groups",
                    include_items_with_no_spend=False,
                    dashapi_cache={},
                ),
                mock.call(
                    user=self.user,
                    breakdown=["publisher_id"],
                    constraints=mock.ANY,
                    goals=mock.ANY,
                    order="-e_media_cost",
                    offset=reports.BATCH_ROWS,
                    limit=reports.BATCH_ROWS,
                    level="ad_groups",
                    include_items_with_no_spend=False,
                    dashapi_cache={},
                ),
            ]
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_raw_new_report_options(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Publisher"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
            "options": {
                "show_archived": True,
                "show_blacklisted_publishers": "active",
                "include_totals": True,
                "include_items_with_no_spend": True,
                "all_accounts_in_local_currency": False,
                "order": "Clicks",
            },
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["publisher_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=True,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["publisher_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="clicks",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="ad_groups",
            include_items_with_no_spend=True,
            dashapi_cache={},
        )
        self.assertTrue(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_breakdown(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [
                {"field": "Account"},
                {"field": "Campaign Id"},
                {"field": "Ad Group"},
                {"field": "Content Ad Id"},
                {"field": "Media Source"},
                {"field": "Day"},
            ],
            "filters": [
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id", "day"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id", "day"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="all_accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_all_account(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Account"}],
            "filters": [
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["account_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["account_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="all_accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_account(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Campaign"}],
            "filters": [
                {"field": "Account Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["campaign_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            account_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["campaign_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_accounts(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Campaign"}],
            "filters": [
                {"field": "Account Id", "operator": "IN", "values": ["1", "2", "3"]},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["campaign_id", "account_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            account_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["campaign_id", "account_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="all_accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_campaign(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Ad Group"}],
            "filters": [
                {"field": "Campaign Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["ad_group_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            campaign_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["ad_group_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="campaigns",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_campaigns(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Ad Group"}],
            "filters": [
                {"field": "Campaign Id", "operator": "IN", "values": ["1", "2", "3"]},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["ad_group_id", "campaign_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            campaign_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["ad_group_id", "campaign_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="accounts",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_ad_group(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Content Ad"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["content_ad_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="ad_groups",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_ad_groups(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Content Ad"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "IN", "values": ["1", "2", "3"]},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["content_ad_id", "ad_group_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            ad_group_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id", "ad_group_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="campaigns",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_report_content_ads(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Content Ad"}],
            "filters": [
                {"field": "Content Ad Id", "operator": "IN", "values": ["1", "2", "3"]},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
                {"field": "Media Source", "operator": "IN", "values": ["1"]},
            ],
        }
        self.report_job.query = query
        ReportJobExecutor.get_report(self.report_job)

        mock_prepare_constraints.assert_called_with(
            self.user,
            ["content_ad_id"],
            datetime.date(2016, 10, 10),
            datetime.date(2016, 10, 10),
            utils.test_helper.QuerySetMatcher(core.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            filtered_businesses=None,
            content_ad_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=reports.BATCH_ROWS,
            level="ad_groups",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_no_dimensions(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            "fields": [{"field": "Total Spend"}],
            "filters": [{"field": "Date", "operator": "=", "value": "2016-10-10"}],
        }
        self.report_job.query = query
        with self.assertRaises(utils.exc.ValidationError):
            ReportJobExecutor.get_report(self.report_job)
