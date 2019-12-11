import functools

from django.db import transaction

import core.models
import restapi.access
import utils.converters
import utils.exc
from restapi.account.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet

UPDATABLE_SETTINGS_FIELDS = (
    "name",
    "archived",
    "whitelist_publisher_groups",
    "blacklist_publisher_groups",
    "frequency_capping",
    "default_icon",
)


class AccountViewSet(RESTAPIBaseViewSet):
    serializer = serializers.AccountSerializer

    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        return self.response_ok(self.serializer(account, context={"request": request}).data)

    def put(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data.get("settings", {})

        with transaction.atomic():
            settings = self._process_default_icon(settings, account, serializer.validated_data)
            settings_valid = {key: value for key, value in list(settings.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            self._update_account(request, account, settings_valid)

        return self.response_ok(self.serializer(account, context={"request": request}).data)

    def list(self, request):
        accounts = core.models.Account.objects.all().filter_by_user(request.user)
        if not utils.converters.x_to_bool(request.GET.get("includeArchived")):
            accounts = accounts.exclude_archived()
        return self.response_ok(self.serializer(accounts, many=True, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
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
            settings = serializer.validated_data.get("settings", {})
            settings = self._process_default_icon(settings, new_account, serializer.validated_data)
            settings_valid = {key: value for key, value in list(settings.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            self._update_account(request, new_account, settings_valid)

        return self.response_ok(self.serializer(new_account, context={"request": request}).data, status=201)

    @staticmethod
    def _process_default_icon(settings, account, data):
        if data.get("default_icon_base64"):
            icon_create_fn = functools.partial(
                core.models.ImageAsset.objects.create_from_image_base64, data["default_icon_base64"], account.id
            )

        elif data.get("default_icon_url"):
            icon_create_fn = functools.partial(
                core.models.ImageAsset.objects.create_from_origin_url, data["default_icon_url"]
            )

        else:
            return settings

        try:
            settings["default_icon"] = icon_create_fn()

        except (
            core.models.image_asset.exceptions.ImageAssetExternalValidationFailed,
            core.models.image_asset.exceptions.ImageAssetInvalid,
        ):
            raise utils.exc.ValidationError(errors={"default_icon_url": ["Could not be processed."]})

        return settings

    @staticmethod
    def _update_account(request, account, data):
        try:
            account.settings.update(request, **data)

        except core.models.settings.account_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.models.settings.account_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})

        except (
            core.models.settings.account_settings.exceptions.DefaultIconNotSquare,
            core.models.settings.account_settings.exceptions.DefaultIconTooSmall,
            core.models.settings.account_settings.exceptions.DefaultIconTooBig,
        ) as err:
            raise utils.exc.ValidationError(errors={"default_icon_url": [str(err)]})
