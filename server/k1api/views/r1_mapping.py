import logging

import dash.constants
import dash.models
from utils import db_for_reads

from .base import K1APIView

logger = logging.getLogger(__name__)


class R1MappingView(K1APIView):
    @db_for_reads.use_read_replica()
    def get(self, request):
        accounts = [int(account) for account in request.GET.getlist("account")]

        data = {account: {"slugs": [], "ad_groups": {}} for account in accounts}

        conversion_pixels = dash.models.ConversionPixel.objects.filter(account_id__in=accounts).filter(archived=False)
        for conversion_pixel in conversion_pixels:
            data[conversion_pixel.account_id]["slugs"].append(conversion_pixel.slug)

        ad_groups = (
            dash.models.AdGroup.objects.all()
            .exclude_archived()
            .select_related("campaign")
            .filter(campaign__account_id__in=accounts)
        )
        for ad_group in ad_groups:
            data[ad_group.campaign.account_id]["ad_groups"][ad_group.id] = {"campaign_id": ad_group.campaign_id}

        return self.response_ok(data)
