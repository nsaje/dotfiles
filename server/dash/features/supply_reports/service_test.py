import datetime

import mock
from django.test import TestCase

import backtosql
import dash.models
from dash.features.supply_reports import service

month_start = datetime.datetime(2020, 2, 1)
month_start_str = month_start.strftime("%Y-%m-%d")
yesterday = month_start + datetime.timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d")
today = month_start + datetime.timedelta(days=2)
today_str = today.strftime("%Y-%m-%d")


@mock.patch("utils.dates_helper.local_today", lambda: today)
class TestSupplyReportsService(TestCase):

    fixtures = ["test_api.yaml"]

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports(self, mock_send_supply_report_email, mock_get_source_stats_from_query):

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        service.send_supply_reports()
        random_recipient = dash.models.SupplyReportRecipient.objects.get(pk=3)
        self.assertEquals(random_recipient.last_sent_dt.date(), datetime.date.today())

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)

        mock_send_supply_report_email.assert_has_calls(
            [
                mock.call("example.a@source.one", yesterday, 1234, 1.1, "Subject", None, None, None, None),
                mock.call("example.b@source.one", yesterday, 1234, 1.1, "", None, None, None, None),
                mock.call("example.c@source.two", yesterday, 0, 0, "Subject", None, None, None, None),
            ],
            any_order=True,
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_skip_sent(self, mock_send_supply_report_email, mock_get_source_stats_from_query):

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        dash.models.SupplyReportRecipient.objects.filter(pk__in=[2, 3]).update(last_sent_dt=datetime.datetime.now())
        dash.models.SupplyReportRecipient.objects.filter(pk=1).update(
            last_sent_dt=datetime.datetime.now() - datetime.timedelta(1)
        )

        service.send_supply_reports(skip_already_sent=True)

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)

        mock_send_supply_report_email.assert_called_once_with(
            "example.a@source.one", yesterday, 1234, 1.1, "Subject", None, None, None, None
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_filter_recipients(self, mock_send_supply_report_email, mock_get_source_stats_from_query):

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            },
            ("gravity",): {
                month_start: {"impressions": 500, "cost": 0.2},
                yesterday: {"impressions": 321, "cost": 0.15},
            },
        }

        service.send_supply_reports(recipient_ids=[3])
        first_recipient = dash.models.SupplyReportRecipient.objects.get(pk=3)
        self.assertEquals(first_recipient.last_sent_dt.date(), datetime.date.today())
        skipped_recipient = dash.models.SupplyReportRecipient.objects.get(pk=1)
        self.assertEquals(skipped_recipient.last_sent_dt, None)

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_send_supply_report_email.assert_has_calls(
            [mock.call("example.c@source.two", yesterday, 321, 0.15, "Subject", None, None, None, None)], any_order=True
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_overwrite_recipients(
        self, mock_send_supply_report_email, mock_get_source_stats_from_query
    ):

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        service.send_supply_reports(overwrite_recipients_email="example@outbrain.com")
        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_send_supply_report_email.assert_has_calls(
            [
                mock.call("example@outbrain.com", yesterday, 1234, 1.1, "Subject", None, None, None, None),
                mock.call("example@outbrain.com", yesterday, 1234, 1.1, "", None, None, None, None),
                mock.call("example@outbrain.com", yesterday, 0, 0, "Subject", None, None, None, None),
            ],
            any_order=True,
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_dryrun(self, mock_send_supply_report_email, mock_get_source_stats_from_query):

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        service.send_supply_reports(dry_run=True)

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        self.assertFalse(mock_send_supply_report_email.called)

    @mock.patch("dash.features.supply_reports.service._get_publisher_stats", autospec=True)
    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_publisher_stats(
        self, mock_send_supply_report_email, mock_get_source_stats_from_query, mock_get_publisher_stats
    ):
        publishers_stats = [[yesterday_str, "pub1.one", 1000, 0.95], [yesterday_str, "pub2.one", 234, 0.15]]
        publishers_report = service._create_csv(["Date", "Publisher", "Impressions", "Spend"], publishers_stats)
        mock_get_publisher_stats.return_value = publishers_stats
        mock_get_source_stats_from_query.return_value = {
            ("gravity",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        recipient = dash.models.SupplyReportRecipient.objects.get(pk=3)
        recipient.publishers_report = True
        recipient.save()

        service.send_supply_reports()

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_get_publisher_stats.assert_called_once_with(recipient, yesterday_str)
        mock_send_supply_report_email.assert_has_calls(
            [
                mock.call("example.a@source.one", yesterday, 0, 0, "Subject", None, None, None, None),
                mock.call("example.b@source.one", yesterday, 0, 0, "", None, None, None, None),
                mock.call("example.c@source.two", yesterday, 1234, 1.1, "Subject", publishers_report, None, None, None),
            ],
            any_order=True,
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_mtd_report(self, mock_send_supply_report_email, mock_get_source_stats_from_query):
        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }
        recipient = dash.models.SupplyReportRecipient.objects.get(pk=1)
        recipient.mtd_report = True
        recipient.save()

        service.send_supply_reports()

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_send_supply_report_email.assert_has_calls(
            [
                mock.call("example.a@source.one", yesterday, 1234, 1.1, "Subject", None, 2234, 1.6, None),
                mock.call("example.b@source.one", yesterday, 1234, 1.1, "", None, None, None, None),
                mock.call("example.c@source.two", yesterday, 0, 0, "Subject", None, None, None, None),
            ],
            any_order=True,
        )

    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_daily_breakdown_report(
        self, mock_send_supply_report_email, mock_get_source_stats_from_query
    ):
        daily_breakdown_stats = [[month_start, 1000, 0.5], [yesterday, 1234, 1.1]]
        daily_breakdown_report = service._create_csv(["Date", "Impressions", "Spend"], daily_breakdown_stats)

        mock_get_source_stats_from_query.return_value = {
            ("adsnative",): {
                month_start: {"impressions": 1000, "cost": 0.5},
                yesterday: {"impressions": 1234, "cost": 1.1},
            }
        }

        recipient = dash.models.SupplyReportRecipient.objects.get(pk=1)
        recipient.daily_breakdown_report = True
        recipient.save()

        service.send_supply_reports()

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_send_supply_report_email.assert_has_calls(
            [
                mock.call(
                    "example.a@source.one", yesterday, 1234, 1.1, "Subject", None, None, None, daily_breakdown_report
                ),
                mock.call("example.b@source.one", yesterday, 1234, 1.1, "", None, None, None, None),
                mock.call("example.c@source.two", yesterday, 0, 0, "Subject", None, None, None, None),
            ],
            any_order=True,
        )

    @mock.patch("dash.features.supply_reports.service._get_publisher_stats", autospec=True)
    @mock.patch("dash.features.supply_reports.service._get_source_stats_from_query", autospec=True)
    @mock.patch("dash.features.supply_reports.service._get_source_stats_for_outbrain_publishers", autospec=True)
    @mock.patch("dash.features.supply_reports.service.send_supply_report_email", autospec=True)
    def test_send_supply_reports_outbrain_publisher_ids(
        self,
        mock_send_supply_report_email,
        mock_get_source_stats_for_outbrain_publishers,
        mock_get_source_stats_from_query,
        mock_get_publisher_stats,
    ):
        daily_breakdown_stats = [[month_start, 1000, 0.5], [yesterday, 1234, 1.1]]
        daily_breakdown_report = service._create_csv(["Date", "Impressions", "Spend"], daily_breakdown_stats)

        publishers_stats = [[yesterday, "pub1.one", 1000, 0.95], [yesterday, "pub2.one", 234, 0.15]]
        publishers_report = service._create_csv(["Date", "Publisher", "Impressions", "Spend"], publishers_stats)
        mock_get_publisher_stats.return_value = publishers_stats

        mock_get_source_stats_from_query.return_value = {}

        mock_get_source_stats_for_outbrain_publishers.return_value = {
            month_start: {"impressions": 1000, "cost": 0.5},
            yesterday: {"impressions": 1234, "cost": 1.1},
        }

        recipient = dash.models.SupplyReportRecipient.objects.get(pk=1)
        recipient.outbrain_publisher_ids = ["111", "222"]
        recipient.daily_breakdown_report = True
        recipient.mtd_report = True
        recipient.publishers_report = True
        recipient.save()

        service.send_supply_reports(recipient_ids=[1])

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_send_supply_report_email.assert_called_with(
            "example.a@source.one",
            yesterday,
            1234,
            1.1,
            "Subject",
            publishers_report,
            2234,
            1.6,
            daily_breakdown_report,
        )


@mock.patch("utils.dates_helper.local_today", lambda: today)
class TestPartnerStatsQuery(TestCase):
    fixtures = ["test_api.yaml"]

    def test_all_source_stats(self):
        query = backtosql.generate_sql(
            "sql/query_partnerstats.sql",
            dict(breakdown="date, exchange", start_date="2020-05-01", end_date="2020-05-10"),
        )
        self.assertEqual(
            query,
            """SELECT date, exchange,
       SUM(impressions) AS impressions,
       SUM(clicks) AS clicks,
       SUM(spend) AS spend
FROM (
  SELECT date,
         exchange,
         publisher,
         SUM(impressions) as impressions,
         SUM(clicks) AS clicks,
         SUM(ssp_cost_nano::decimal)/1e9 as spend
  FROM partnerstats
  WHERE 1=1

  GROUP BY 1, 2, 3
) stats
WHERE date BETWEEN '2020-05-01' AND '2020-05-10'
GROUP BY date, exchange
ORDER BY date, exchange""",
        )

    def test_publisher_stats(self):
        query = backtosql.generate_sql(
            "sql/query_partnerstats.sql",
            dict(
                breakdown="date, publisher",
                bidder_slug="triplelift",
                outbrain_publisher_ids="",
                start_date="2020-05-01",
                end_date="2020-05-01",
            ),
        )
        self.assertEqual(
            query,
            """SELECT date, publisher,
       SUM(impressions) AS impressions,
       SUM(clicks) AS clicks,
       SUM(spend) AS spend
FROM (
  SELECT date,
         exchange,
         publisher,
         SUM(impressions) as impressions,
         SUM(clicks) AS clicks,
         SUM(ssp_cost_nano::decimal)/1e9 as spend
  FROM partnerstats
  WHERE exchange = 'triplelift'

  GROUP BY 1, 2, 3
) stats
WHERE date BETWEEN '2020-05-01' AND '2020-05-01'
GROUP BY date, publisher
ORDER BY date, publisher""",
        )

    def test_source_stats_with_ob(self):
        query = backtosql.generate_sql(
            "sql/query_partnerstats.sql",
            dict(
                breakdown="date",
                bidder_slug="triplelift",
                outbrain_publisher_ids="'1','2'",
                start_date="2020-05-01",
                end_date="2020-05-01",
            ),
        )
        self.assertEqual(
            query,
            """SELECT date,
       SUM(impressions) AS impressions,
       SUM(clicks) AS clicks,
       SUM(spend) AS spend
FROM (
  SELECT date,
         exchange,
         publisher,
         SUM(impressions) as impressions,
         SUM(clicks) AS clicks,
         SUM(ssp_cost_nano::decimal)/1e9 as spend
  FROM partnerstats
  WHERE exchange = 'triplelift'

        AND outbrain_publisher_id IN ('1','2')

  GROUP BY 1, 2, 3
) stats
WHERE date BETWEEN '2020-05-01' AND '2020-05-01'
GROUP BY date
ORDER BY date""",
        )
