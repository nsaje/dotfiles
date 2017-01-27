from utils.command_helpers import ExceptionCommand
import datetime

from etl import maintenance
from etl import refresh_k1


class Command(ExceptionCommand):

    help = "Output and log comparison of traffic between stats, contentadstats and mv_master"

    def add_arguments(self, parser):
        parser.add_argument('from', type=str)

    def handle(self, *args, **options):
        date_from = datetime.datetime.strptime(options['from'], '%Y-%m-%d').date()
        date_to = datetime.date.today()
        results = maintenance.crossvalidate_traffic(date_from, date_to)

        print "Comparison of statistics between {} and {}".format(date_from.isoformat(), date_to.isoformat())
        print "-" * 40
        print "Clicks: {:d}".format(results.clicks)
        print "stats.clicks - contentadstats.clicks = {:d}".format(results.diff_s_ca_clicks)
        print "stats.clicks - mv_master.clicks = {:d}".format(results.diff_s_mv_clicks)
        print "-" * 40
        print "Impressions: {:d}".format(results.impressions)
        print "stats.impressions - contentadstats.impressions = {:d}".format(results.diff_s_ca_impressions)
        print "stats.impressions - mv_master.impressions = {:d}".format(results.diff_s_mv_impressions)
        print "-" * 40
        print "Spend: {:.2f}".format(float(results.spend_micro) / 10e6)
        print "stats.spend - contentadstats.spend = {:.2f} (some error is normal - micro to cc conversion)".format(
            float(results.diff_s_ca_spend_micro) / 10e6)
        print "stats.spend - mv_master.spend = {:.2f}".format(float(results.diff_s_mv_spend_micro) / 10e6)
        print "-" * 40
        print "Data spend {:.2f}".format(float(results.data_spend_micro) / 10e6)
        print "stats.data_spend - contentadstats.data_spend = {:.2f}".format(
            float(results.diff_s_ca_data_spend_micro) / 10e6)
        print "stats.data_spend - mv_master.data_spend = {:.2f}".format(
            float(results.diff_s_mv_data_spend_micro) / 10e6)
        print "# Effective spend"
        print "contentadstats.effective_spend - mv_master.effective_spend = {:.2f}".format(
            float(results.diff_s_mv_data_spend_micro) / 10e6)
        print "-" * 40
        print "Spend: {:.2f}".format(results.spend_nano / 10e9)
        print "Effective cost: {:.2f}".format(results.effective_cost_nano / 10e9)
        print "Overspend: {:.2f}".format(results.overspend_nano / 10e9)
