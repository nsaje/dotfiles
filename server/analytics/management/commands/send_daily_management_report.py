import datetime

import analytics.management_report
import utils.email_helper
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.command_helpers import set_logger_verbosity

logger = zlogging.getLogger(__name__)


class Command(Z1Command):

    help = "Sends daily management report email"

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        data = analytics.management_report.get_query_results()
        if data:
            yesterday = datetime.date.today() - datetime.timedelta(1)
            html = analytics.management_report.get_daily_report_html(data)
            attachment = {
                "filename": "report-{}.csv".format(yesterday),
                "mimetype": "text/csv",
                "content": analytics.management_report.prepare_report_as_csv(data),
            }
            utils.email_helper.send_daily_management_report_email(html, attachment)
