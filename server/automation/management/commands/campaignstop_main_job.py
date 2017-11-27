import automation.campaignstop.service

from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        automation.campaignstop.service.refresh_realtime_data()
