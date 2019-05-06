from django.db import transaction

import core.models
import restapi.access
import utils.converters
import utils.exc
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers

UPDATABLE_SETTINGS_FIELDS = (
    "name",
    "archived",
    "whitelist_publisher_groups",
    "blacklist_publisher_groups",
    "frequency_capping",
)


class AccountViewSet(RESTAPIBaseViewSet):
    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        return self.response_ok(serializers.AccountSerializer(account, context={"request": request}).data)

    def put(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.AccountSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings_updates = serializer.validated_data.get("settings")
        if settings_updates:
            update = {key: value for key, value in list(settings_updates.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            self._update_account(request, account, update)
        return self.response_ok(serializers.AccountSerializer(account, context={"request": request}).data)

    def list(self, request):
        accounts = core.models.Account.objects.all().filter_by_user(request.user)
        if not utils.converters.x_to_bool(request.GET.get("includeArchived")):
            accounts = accounts.exclude_archived()
        return self.response_ok(serializers.AccountSerializer(accounts, many=True, context={"request": request}).data)

    def create(self, request):
        serializer = serializers.AccountSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        agency = None
        agency_id = serializer.validated_data.get("agency_id")
        if agency_id:
            agency = restapi.access.get_agency(request.user, agency_id)

        with transaction.atomic():
            new_account = core.models.Account.objects.create(
                request,
                name=serializer.validated_data.get("settings", {}).get("name"),
                agency=agency,
                currency=serializer.validated_data.get("currency"),
            )
            settings_updates = serializer.validated_data.get("settings")
            if settings_updates:
                update = {
                    key: value for key, value in list(settings_updates.items()) if key in UPDATABLE_SETTINGS_FIELDS
                }
                self._update_account(request, new_account, update)

        return self.response_ok(
            serializers.AccountSerializer(new_account, context={"request": request}).data, status=201
        )

    def _update_account(self, request, account, data):
        try:
            account.settings.update(request, **data)

        except core.models.settings.account_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.models.settings.account_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
