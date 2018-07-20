import core.direct_deals

from .base import K1APIView


class DirectDealsView(K1APIView):
    def get(self, request):
        deal_connections = (
            core.direct_deals.DirectDealConnection.objects.select_related("source").prefetch_related("deals").all()
        )

        return self.response_ok(
            [
                {
                    "exchange": deal_connection.source.bidder_slug,
                    "exclusive": deal_connection.exclusive,
                    "adgroup_id": deal_connection.adgroup_id,
                    "agency_id": deal_connection.agency_id,
                    "deals": [deal.deal_id for deal in deal_connection.deals.all()],
                }
                for deal_connection in deal_connections
            ]
        )
