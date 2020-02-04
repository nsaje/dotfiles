import core.models
import utils.exc
from serviceapi import base
from utils.rest_common import authentication

from . import serializers

SEAT_INFO_SERVICE_NAME = "seatinfo"


class SeatInfoView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(SEAT_INFO_SERVICE_NAME),)
    serializer = serializers.SeatSerializer

    def get(self, request, seat_id):
        try:
            account = core.models.Account.objects.get(id=seat_id)
            return self.response_ok(data=self.serializer(account).data)
        except core.models.Account.DoesNotExist:
            raise utils.exc.MissingDataError("Account does not exist")
