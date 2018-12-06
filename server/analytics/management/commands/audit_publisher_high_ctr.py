import datetime

import analytics.monitor
import utils.command_helpers
import utils.slack

MESSAGE = "Publisher <http://redash.zemanta.com:8123/dashboard/publisher-view-dashboard?p_publisher={publisher}|{publisher}> had a CTR of *{ctr}%* on {date} and that looks suspicious."  # noqa
HELPER_LINKS = "Those links might help you in your investigation : <http://redash.zemanta.com:8123/queries/575#table|Publisher CTR past 7 days> <http://redash.zemanta.com:8123/queries/576?p_date_compact={compact_date}| Publishers CTR by date>."  # noqa


class Command(utils.command_helpers.ExceptionCommand):
    def add_arguments(self, parser):
        parser.add_argument("--date", dest="date", help="Date %Y-%m-%d")
        parser.add_argument("--ctr", dest="ctr", default=3, help="CTR threshold")
        parser.add_argument("--max_clicks", dest="max_clicks", default=100, help="Clicks threshold")
        parser.add_argument("--max_impressions", dest="max_impressions", default=100, help="Impressions threshold")
        parser.add_argument("--slack", dest="slack", help="Post alert on Slack", action="store_true")

    def handle(self, *args, **options):
        yesterday = datetime.date.today() - datetime.timedelta(1)
        self.slack = options["slack"]
        self.date = datetime.datetime.strptime(options["date"], "%Y-%m-%d").date() or yesterday
        self.max_clicks = options["max_clicks"]
        self.max_impressions = options["max_impressions"]
        self.ctr = options["ctr"]

        if self.date > datetime.date.today():
            return "Date must be before today"

        alerts = analytics.monitor.publisher_high_ctr(
            date=self.date, ctr_threshold=self.ctr, max_clicks=self.max_clicks, max_impressions=self.max_impressions
        )

        if not alerts:
            return
        messages = [MESSAGE.format(**i) for i in alerts]
        text = "\n".join(messages)
        msg = "\n".join([text, HELPER_LINKS.format(compact_date=self.date.strftime("%y%m%d"))])

        if self.slack:
            try:
                utils.slack.publish(
                    msg, channel="z1-monitor", username="Fraud alert", msg_type=utils.slack.MESSAGE_TYPE_WARNING
                )
            except Exception as e:
                raise e
        self.stdout.write(msg)
