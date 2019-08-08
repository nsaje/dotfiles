import rest_framework.permissions
from django.db import transaction

import core.models
import restapi.access
import restapi.account.v1.views
import utils.exc

from . import helpers
from . import serializers


class AccountViewSet(restapi.account.v1.views.AccountViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AccountSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def defaults(self, request):
        agency = core.models.Agency.objects.all().filter_by_user(request.user).first()
        account = core.models.Account.objects.get_default(request, agency)
        extra_data = helpers.get_extra_data(request.user, account)
        return self.response_ok(
            data=self.serializer(account, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        extra_data = helpers.get_extra_data(request.user, account)
        return self.response_ok(
            data=self.serializer(account, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def put(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data.get("settings")

        with transaction.atomic():
            self._update_account(request, account, settings)

        return self.response_ok(self.serializer(account, context={"request": request}).data)

    def create(self, request):
        if not request.user.has_perm("zemauth.all_accounts_accounts_add_account"):
            raise utils.exc.AuthorizationError()

        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        agency_id = serializer.validated_data.get("agency_id")
        agency = restapi.access.get_agency(request.user, agency_id) if agency_id is not None else None

        with transaction.atomic():
            new_account = core.models.Account.objects.create(
                request,
                name=serializer.validated_data.get("settings", {}).get("name"),
                agency=agency,
                currency=serializer.validated_data.get("currency"),
            )
            settings = serializer.validated_data.get("settings")
            self._update_account(request, new_account, settings)

        return self.response_ok(self.serializer(new_account, context={"request": request}).data, status=201)
