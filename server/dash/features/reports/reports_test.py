import datetime
from decimal import Decimal

import mock
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.test import TestCase

import core.models
import dash.constants
import utils.test_helper
from dash.features import scheduled_reports
from utils.magic_mixer import magic_mixer

from . import constants
from . import reports
from .reportjob import ReportJob
from .reports import ReportJobExecutor


class ReportsExecuteTest(TestCase):
    def setUp(self):
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = magic_mixer.blend_user()
        self.reportJob.save()

        influx_incr_patcher = mock.patch("influx.incr")
        self.mock_influx_incr = influx_incr_patcher.start()
        self.addCleanup(influx_incr_patcher.stop)

    def assertJobFailed(self, status, result, exception=None):
        self.mock_influx_incr.assert_called_once_with("dash.reports", 1, status=status)

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual(result, self.reportJob.result)
        if exception is not None:
            self.assertIn(str(exception), self.reportJob.exception)

    @mock.patch("dash.features.reports.reports.ReportJobExecutor._send_fail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_handle_exception(self, mock_get_report, mock_send_fail):
        e = Exception("test-error")
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed(
            "failed", "Internal Error: Please contact support. Report job ID is %d." % self.reportJob.id, e
        )

    @mock.patch("dash.features.reports.reports.ReportJobExecutor._send_fail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_handle_soft_time_limit(self, mock_get_report, mock_send_fail):
        e = SoftTimeLimitExceeded()
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed(
            "timeout", "Job Timeout: Requested report probably too large. Report job ID is %d." % self.reportJob.id
        )

    @mock.patch("utils.dates_helper.utc_now")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor._send_fail")
    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_too_old(self, mock_get_report, mock_send_fail, mock_now):
        mock_get_report.side_effect = Exception("test-error")
        mock_now.return_value = datetime.datetime(2017, 8, 1, 11, 31)

        self.reportJob.created_dt = datetime.datetime(2017, 8, 1, 10, 30)
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed("too_old", "Service Timeout: Please try again later.")

    @mock.patch("dash.features.reports.reports.ReportJobExecutor.get_report")
    def test_incorrect_state(self, mock_get_report):
        mock_get_report.side_effect = Exception("test-error")

        self.reportJob.status = constants.ReportJobStatus.DONE
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()

    @mock.patch("utils.email_helper.send_async_report_fail")
    def test_send_fail(self, mock_send):
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.reportJob.user])
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

        executor = reports.ReportJobExecutor(self.reportJob)
        executor._send_fail()

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

        executor = reports.ReportJobExecutor(self.reportJob)
        executor._send_fail()

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
        agency = magic_mixer.blend(core.models.Agency, default_csv_decimal_separator=",", default_csv_separator=";")
        self.reportJob.user.agency_set.add(agency)

        self.reportJob.query = {}
        self.reportJob.query["options"] = {}
        self.assertEqual(ReportJobExecutor._get_csv_separators(self.reportJob), (";", ","))

        self.reportJob.query["options"]["csv_separator"] = "\t"
        self.reportJob.query["options"]["csv_decimal_separator"] = "."
        self.assertEqual(ReportJobExecutor._get_csv_separators(self.reportJob), ("\t", "."))


class ReportsGetReportCSVTest(TestCase):
    def setUp(self):
        magic_mixer.blend(core.features.publisher_groups.PublisherGroup, id=settings.GLOBAL_BLACKLIST_ID)
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = magic_mixer.blend_user()
        self.reportJob.save()
        utils.test_helper.add_permissions(self.reportJob.user, ["can_request_accounts_report_in_local_currencies"])

        influx_incr_patcher = mock.patch("influx.incr")
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
        expected = """"Ad Group Id","Total Spend","Clicks","Status (2019-02-26)","Currency"\r\n"1","12.3000","5","ACTIVE","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_currency(self, mock_query):
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account__currency="EUR", campaign__account__uses_bcm_v2=True
        )
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
        magic_mixer.blend(core.models.Account, currency="EUR", id=1, users=self.reportJob.user, uses_bcm_v2=True)
        magic_mixer.blend(core.models.Account, currency="USD", id=2, users=self.reportJob.user, uses_bcm_v2=True)
        mock_query.return_value = [
            {"account_id": 1, "etfm_cost": Decimal("12.3"), "local_etfm_cost": Decimal("15.4"), "clicks": 5},
            {"account_id": 2, "etfm_cost": Decimal("13.4"), "local_etfm_cost": Decimal("16.4"), "clicks": 8},
        ]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Account Id","Total Spend","Clicks","Currency"\r\n"1","15.4000","5","EUR"\r\n"2","16.4000","8","USD"\r\n"""
        self.assertEqual(expected, output)

    @mock.patch("stats.api_reports.query")
    def test_csv_config(self, mock_query):
        self.reportJob.query = self.build_query(
            ["Ad Group Id", "Total Spend", "Clicks"], csv_separator=";", csv_decimal_separator=","
        )
        row = {"ad_group_id": 1, "etfm_cost": Decimal("12.3"), "clicks": 5}
        mock_query.return_value = [row]
        output, filename = ReportJobExecutor.get_report(self.reportJob)
        expected = """"Ad Group Id";"Total Spend";"Clicks";"Currency"\r\n"1";"12,3000";"5";"USD"\r\n"""
        self.assertEqual(expected, output)


class ReportsImplementationTest(TestCase):
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
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["publisher_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
            level="ad_groups",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch("stats.api_reports.get_filename", return_value="")
    @mock.patch("stats.api_reports.totals", return_value={})
    @mock.patch("stats.api_reports.query", return_value=[])
    @mock.patch("stats.api_reports.prepare_constraints")
    def test_raw_new_report_batch(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        mock_query.side_effect = [[{}] * 10000, [{}] * 100]
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
                    limit=10000,
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
                    offset=10000,
                    limit=10000,
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
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["publisher_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="clicks",
            offset=0,
            limit=10000,
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
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id", "day"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["account_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            account_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["campaign_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            account_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["campaign_id", "account_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            campaign_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["ad_group_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            campaign_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["ad_group_id", "campaign_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            ad_group_ids=[1],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            ad_group_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id", "ad_group_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
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
            content_ad_ids=[1, 2, 3],
        )

        mock_query.assert_called_with(
            user=self.user,
            breakdown=["content_ad_id"],
            constraints=mock.ANY,
            goals=mock.ANY,
            order="-e_media_cost",
            offset=0,
            limit=10000,
            level="ad_groups",
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)
