import datetime
import logging

from k1api.views import ga_accounts
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Request:
    GET = {}


class Command(Z1Command):
    help = "Load k1api ga accounts into cache"

    def handle(self, *args, **options):
        today = datetime.date.today()
        view = ga_accounts.GAAccountsView()
        request = Request()
        for date in (today - datetime.timedelta(days=n) for n in range(4)):
            date_since = date.strftime("%Y-%m-%d")
            logger.info("loading for %s", date_since)
            request.GET["date_since"] = date_since
            view.get(request)
