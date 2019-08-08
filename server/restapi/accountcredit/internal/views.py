import restapi.accountcredit.v1.views

from . import serializers


class AccountCreditViewSet(restapi.accountcredit.v1.views.AccountCreditViewSet):
    serializer = serializers.AccountCreditSerializer
