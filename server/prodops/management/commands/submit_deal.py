from django.db import transaction
from django.db.models import Q

import dash.models
import utils.command_helpers


class Command(utils.command_helpers.Z1Command):
    help = "Create a custom deal"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str)
        parser.add_argument("deal_id", type=str)
        parser.add_argument("--agencies", dest="agencies", default="")
        parser.add_argument("--accounts", dest="accounts", default="")
        parser.add_argument("--campaigns", dest="campaigns", default="")
        parser.add_argument("--ad-groups", dest="ad_groups", default="")
        parser.add_argument("--not-exclusive", dest="not_exclusive", action="store_true", default=False)

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def _clean_ids(self, raw):
        return raw and set(map(int, [x.strip() for x in raw.split(",") if x.strip()])) or set()

    def handle(self, *args, **options):
        agency_ids = self._clean_ids(options["agencies"])
        account_ids = self._clean_ids(options["accounts"])
        campaign_ids = self._clean_ids(options["campaigns"])
        ad_group_ids = self._clean_ids(options["ad_groups"])

        agencies = dash.models.Agency.objects.filter(pk__in=agency_ids)
        ad_groups = dash.models.AdGroup.objects.filter(
            Q(pk__in=ad_group_ids) | Q(campaign_id__in=campaign_ids) | Q(campaign__account_id__in=account_ids)
        )
        if not (agencies or ad_groups):
            self._print("No entitites connected")
            return
        source_id = options["source"]
        source = None
        if source_id.isdigit():
            source = dash.models.Source.objects.get(id=int(source_id))
        elif source_id:
            source = dash.models.Source.objects.get(Q(bidder_slug="b1_{}".format(source_id)) | Q(bidder_slug=source_id))
        if not source:
            self._print("No source.")
            return

        with transaction.atomic():
            deal, created = dash.models.DirectDeal.objects.get_or_create(deal_id=options["deal_id"])
            if created:
                self._print("Deal {} created, linking ...".format(deal.deal_id))
            else:
                self._print("Deal {} already exists, linking ...".format(deal.deal_id))
            for agency in agencies:
                ddc = dash.models.DirectDealConnection.objects.create(
                    source=source, exclusive=not options["not_exclusive"], agency=agency
                )
                ddc.deals.add(deal)
                self._print(" - agency {}: {}".format(agency.pk, agency.name))
            for ad_group in ad_groups:
                ddc = dash.models.DirectDealConnection.objects.create(
                    source=source, exclusive=not options["not_exclusive"], adgroup=ad_group
                )
                ddc.deals.add(deal)
                self._print(" - ad group {}: {}".format(ad_group.pk, ad_group.name))
