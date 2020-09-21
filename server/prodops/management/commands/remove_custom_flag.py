from django.db import transaction

import utils.command_helpers
from core.models import Account
from core.models import AdGroup
from core.models import Agency
from core.models import Campaign
from dash.features.custom_flags import CustomFlag


class Command(utils.command_helpers.Z1Command):
    help = """Remove custom flag"""

    def add_arguments(self, parser):
        parser.add_argument(
            "flag", type=str, choices=[cf.id for cf in CustomFlag.objects.all()], help="Custom flag to remove"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        flag_id = options["flag"]
        flag = CustomFlag.objects.get(id=flag_id)
        objects_cleaned = 0
        models = [Agency, Account, Campaign, AdGroup]
        for mdl in models:
            for obj in mdl.objects.filter(custom_flags__has_key=flag_id):
                del obj.custom_flags[flag_id]
                obj.save(None)
                objects_cleaned += 1
        flag.delete()
        self.stdout.write("Flag {} removed from {} objects.".format(flag_id, objects_cleaned))
