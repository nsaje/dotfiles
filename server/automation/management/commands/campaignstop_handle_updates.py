import influx

import automation.campaignstop
from utils.command_helpers import Z1Command


class Command(Z1Command):
    @influx.timer("campaignstop.job_run", job="handle_updates")
    def handle(self, *args, **options):
        automation.campaignstop.handle_updates()
