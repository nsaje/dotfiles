import datetime

from dcron import models
from utils.command_helpers import Z1Command


class Command(Z1Command):
    help = "Delete DCronJobHistory records for DCronJobs executed before specified date"

    def add_arguments(self, parser):
        parser.add_argument("older_than", type=datetime.datetime.fromisoformat)

    def handle(self, *args, **options):
        older_than = options.get("older_than")
        number_of_deleted, _ = models.DCronJobHistory.objects.filter(executed_dt__lte=older_than).delete()
        self.stdout.write(self.style.SUCCESS("Deleted %s DCronJobHistory records." % number_of_deleted))
