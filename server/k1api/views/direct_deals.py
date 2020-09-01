import core.features.deals
from utils import db_router

from .base import K1APIView


class DirectDealsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        deal_connections = core.features.deals.DirectDealConnection.objects.select_related("deal__source").all()

        return self.response_ok(
            [
                {
                    "exchange": deal_connection.deal.source.bidder_slug,
                    "exclusive": deal_connection.exclusive,
                    "adgroup_id": deal_connection.adgroup_id,
                    "agency_id": deal_connection.agency_id,
                    "account_id": deal_connection.account_id,
                    "campaign_id": deal_connection.campaign_id,
                    "deals": [deal_connection.deal.deal_id],
                }
                for deal_connection in deal_connections
            ]
        )
