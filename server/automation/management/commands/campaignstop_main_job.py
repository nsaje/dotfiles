import automation.campaignstop

from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        automation.campaignstop.refresh_realtime_data()
        automation.campaignstop.update_campaigns_state()
