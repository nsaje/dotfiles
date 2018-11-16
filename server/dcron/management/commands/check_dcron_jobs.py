from django.core.management.base import BaseCommand

from dcron.alerts import handle_alerts


class Command(BaseCommand):
    help = "Check execution of cron jobs defined in DCronJob model."

    def _handle(self, *args, **options):
        handle_alerts()
