import rest_framework.permissions

import restapi.accountcredit.v1.views

from . import serializers


class AccountCreditViewSet(restapi.accountcredit.v1.views.AccountCreditViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AccountCreditSerializer
