import logging

import dash.constants
import dash.features.geolocation
import dash.models
from utils import db_router

from .base import K1APIView

logger = logging.getLogger(__name__)


class GeolocationsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        keys = request.GET.get("keys")
        keys = keys.split(",") if keys else []
        geolocations = dash.features.geolocation.Geolocation.objects.filter(key__in=keys)
        response = geolocations.values("key", "name", "woeid", "outbrain_id")
        return self.response_ok(list(response))
