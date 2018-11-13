from dcron.alerts import handle_alerts
from dcron.commands import DCronCommand


class Command(DCronCommand):
    help = "Check execution of cron jobs defined in DCronJob model."

    def _handle(self, *args, **options):
        handle_alerts()
