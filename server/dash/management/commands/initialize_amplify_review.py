import structlog
from django.db import transaction

from dash import models
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    help = "Initialize Amplify review on an ad group"

    def add_arguments(self, parser):
        parser.add_argument("ad_group_id", type=int)

    def handle(self, *args, **options):
        ad_group = models.AdGroup.objects.get(id=options["ad_group_id"])
        if ad_group.amplify_review:
            self.stdout.write("Amplify review for ad group {} already enabled. Exiting ...\n".format(ad_group.id))
            return

        self.stdout.write("Initializing Amplify review for ad group {}.\n".format(ad_group.id))
        with transaction.atomic():
            ad_group.amplify_review = True
            ad_group.save(None)
            ad_group.contentad_set.update(amplify_review=True)
            ad_group.ensure_amplify_review_source(None)

        self.stdout.write("Done.")
