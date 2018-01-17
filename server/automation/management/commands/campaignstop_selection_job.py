import automation.campaignstop
from utils.command_helpers import ExceptionCommand
from automation.campaignstop.service import refresh_realtime_data


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        refresh_realtime_data()
        automation.campaignstop.mark_almost_depleted_campaigns()
