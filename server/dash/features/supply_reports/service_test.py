import datetime

import mock
from django.test import TestCase

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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
            },
            (2,): {
                month_start_str: {"impressions": 500, "cost": 0.2},
                yesterday_str: {"impressions": 321, "cost": 0.15},
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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
        publishers_stats = [[yesterday_str, "pub1.one", 1000, 1, 0.95], [yesterday_str, "pub2.one", 234, 1, 0.15]]
        publishers_report = service._create_csv(
            ["Date", "Publisher", "Impressions", "Clicks", "Spend"], publishers_stats
        )
        mock_get_publisher_stats.return_value = publishers_stats
        mock_get_source_stats_from_query.return_value = {
            (2,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
            }
        }

        recipient = dash.models.SupplyReportRecipient.objects.get(pk=3)
        recipient.publishers_report = True
        recipient.save()

        service.send_supply_reports()

        mock_get_source_stats_from_query.assert_called_once_with(month_start_str, yesterday_str)
        mock_get_publisher_stats.assert_called_once_with(recipient, yesterday)
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
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
        daily_breakdown_stats = [[month_start_str, 1000, 0.5], [yesterday_str, 1234, 1.1]]
        daily_breakdown_report = service._create_csv(["Date", "Impressions", "Spend"], daily_breakdown_stats)

        mock_get_source_stats_from_query.return_value = {
            (1,): {
                month_start_str: {"impressions": 1000, "cost": 0.5},
                yesterday_str: {"impressions": 1234, "cost": 1.1},
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
        daily_breakdown_stats = [[month_start_str, 1000, 0.5], [yesterday_str, 1234, 1.1]]
        daily_breakdown_report = service._create_csv(["Date", "Impressions", "Spend"], daily_breakdown_stats)

        publishers_stats = [[yesterday_str, "pub1.one", 1000, 1, 0.95], [yesterday_str, "pub2.one", 234, 1, 0.15]]
        publishers_report = service._create_csv(
            ["Date", "Publisher", "Impressions", "Clicks", "Spend"], publishers_stats
        )
        mock_get_publisher_stats.return_value = publishers_stats

        mock_get_source_stats_from_query.return_value = {}

        mock_get_source_stats_for_outbrain_publishers.return_value = {
            month_start_str: {"impressions": 1000, "cost": 0.5},
            yesterday_str: {"impressions": 1234, "cost": 1.1},
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
class TestSupplyReportsServiceHelpers(TestCase):
    fixtures = ["test_api.yaml"]

    def test_custom_stats_query_sql(self):
        rec = dash.models.SupplyReportRecipient.objects.get(pk=1)
        rec.outbrain_publisher_ids = ["123", "456", "789"]
        rec.save()

        result = """select date, sum(impressions) as impressions, sum(clicks) as clicks, sum(spend) as spend
from (
  select convert_timezone('UTC', 'EST',
                          (date || ' ' || hour || ':00:00')::timestamp)::date as date,
         publisher,
         sum(impressions) as impressions,
         sum(clicks) as clicks,
         sum(spend::decimal)/1e6 as spend
  from stats
  where media_source = 'adsnative'
        and outbrain_publisher_id IN ('123','456','789')
        and date >= ('2020-03-15'::date - interval '1 day')
        and date <= ('2020-03-30'::date + interval '1 day')
  group by 1, 2
) stats
where date between '2020-03-15' and '2020-03-30'
group by date
order by date"""
        self.assertEqual(service._get_custom_stats_query(rec, "date", "2020-03-15", "2020-03-30"), result)

        result = """select date,publisher, sum(impressions) as impressions, sum(clicks) as clicks, sum(spend) as spend
from (
  select convert_timezone('UTC', 'EST',
                          (date || ' ' || hour || ':00:00')::timestamp)::date as date,
         publisher,
         sum(impressions) as impressions,
         sum(clicks) as clicks,
         sum(spend::decimal)/1e6 as spend
  from stats
  where media_source = 'adsnative'
        and outbrain_publisher_id IN ('123','456','789')
        and date >= ('2020-03-30'::date - interval '1 day')
        and date <= ('2020-03-30'::date + interval '1 day')
  group by 1, 2
) stats
where date between '2020-03-30' and '2020-03-30'
group by date,publisher
order by date,publisher"""
        self.assertEqual(service._get_custom_stats_query(rec, "date,publisher", "2020-03-30", "2020-03-30"), result)
