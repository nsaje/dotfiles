from restapi.common.views_base import RESTAPIBaseViewSet

import restapi.access
import core.models
import utils.exc

from . import serializers

from django.db import transaction


UPDATABLE_SETTINGS_FIELDS = ("name", "whitelist_publisher_groups", "blacklist_publisher_groups")


class AccountViewSet(RESTAPIBaseViewSet):
    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        return self.response_ok(serializers.AccountSerializer(account).data)

    def put(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.AccountSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        settings_updates = serializer.validated_data.get("settings")
        if settings_updates:
            update = {key: value for key, value in list(settings_updates.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            self._update_account(request, account, update)
        return self.response_ok(serializers.AccountSerializer(account).data)

    def list(self, request):
        accounts = core.models.Account.objects.all().filter_by_user(request.user)
        return self.response_ok(serializers.AccountSerializer(accounts, many=True).data)

    def create(self, request):
        serializer = serializers.AccountSerializer(data=request.data)
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

        return self.response_ok(serializers.AccountSerializer(new_account).data, status=201)

    def _update_account(self, request, account, data):
        try:
            account.settings.update(request, **data)

        except core.models.settings.account_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.models.settings.account_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
