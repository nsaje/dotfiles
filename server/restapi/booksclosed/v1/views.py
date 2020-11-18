import rest_framework.permissions

import etl.materialization_run
import utils.dates_helper
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class BooksClosedViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.BooksClosedSerializer

    def get(self, request):
        date = utils.dates_helper.utc_datetime_to_local_date(etl.materialization_run.get_last_books_closed_date())
        data = {"traffic_data": {"latest_complete_date": date}}
        return self.response_ok(self.serializer(data, context={"request": request}).data)
