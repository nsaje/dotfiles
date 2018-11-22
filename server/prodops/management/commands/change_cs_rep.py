from django.db.models import Q

import utils.command_helpers
import zemauth
from dash import models


class Req:
    pass


class Command(utils.command_helpers.ExceptionCommand):
    help = """Change the CS representative on multiple accounts."""

    def add_arguments(self, parser):
        parser.add_argument("cs_rep", type=str, help="email address of the new CS representative")
        parser.add_argument("--agencies", default="")
        parser.add_argument("--accounts", default="")

    def _clean_ids(self, raw):
        return raw and set(map(int, [x.strip() for x in raw.split(",") if x.strip()])) or set()

    def handle(self, *args, **options):
        agency_ids = self._clean_ids(options["agencies"])
        account_ids = self._clean_ids(options["accounts"])

        cs_rep_mail = options.get("cs_rep")
        cs_rep = zemauth.models.User.objects.get(email=cs_rep_mail)

        accounts = models.Account.objects.filter(Q(pk__in=account_ids) | Q(agency_id__in=agency_ids))

        if bool(agency_ids):
            req = Req()
            req.user = cs_rep
            for agency in models.Agency.objects.filter(pk__in=agency_ids):
                agency.cs_representative = cs_rep
                agency.save(req)

        for account in accounts:
            account.settings.update(None, default_cs_representative=cs_rep)
            self.stdout.write(f"CS representative on  account{account.id} has been set to{cs_rep.email}")
