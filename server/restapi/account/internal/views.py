import rest_framework.permissions
from django.db import transaction

import core.features.deals
import core.models
import dash.constants
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
        self._augment_account(request, account)
        extra_data = helpers.get_extra_data(request.user, account)
        return self.response_ok(
            data=self.serializer(account, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        self._augment_account(request, account)
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
            if "allowed_media_sources" in serializer.validated_data.keys():
                self._handle_allowed_media_sources(
                    request, account, serializer.validated_data.get("allowed_media_sources", [])
                )
            if "deals" in serializer.validated_data.keys():
                self._handle_deals(request, account, serializer.validated_data.get("deals", []))

        self._augment_account(request, account)
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
            self._handle_allowed_media_sources(
                request, new_account, serializer.validated_data.get("allowed_media_sources", [])
            )
            self._handle_deals(request, new_account, serializer.validated_data.get("deals", []))

        self._augment_account(request, new_account)
        return self.response_ok(self.serializer(new_account, context={"request": request}).data, status=201)

    @staticmethod
    def _augment_account(request, account):
        account.allowed_media_sources = []
        if request.user.has_perm("zemauth.can_modify_allowed_sources"):
            account.allowed_media_sources = helpers.get_allowed_sources(request.user, account)
        account.deals = []
        if request.user.has_perm("zemauth.can_see_deals_in_ui"):
            account.deals = account.get_deals()

    @staticmethod
    def _handle_allowed_media_sources(request, account, data):
        allowed_sources = helpers.get_allowed_sources(request.user, account)
        available_sources = helpers.get_available_sources(request.user, account.agency)

        new_allowed_sources = []
        data_dict = dict((x["id"], x) for x in data)
        for available_source in available_sources:
            if data_dict.get(available_source.id) is not None:
                new_allowed_sources.append(available_source)

        allowed_sources_set = set(allowed_sources)
        new_allowed_sources_set = set(new_allowed_sources)

        to_be_removed = allowed_sources_set.difference(new_allowed_sources_set)
        to_be_added = new_allowed_sources_set.difference(allowed_sources_set)

        non_removable_sources_ids = helpers.get_non_removable_sources_ids(account, to_be_removed)
        if len(non_removable_sources_ids) > 0:
            source_names = (
                core.models.Source.objects.filter(id__in=non_removable_sources_ids)
                .order_by("id")
                .values_list("name", flat=True)
            )
            if len(source_names) > 1:
                error_message = "Can't save changes because media sources {} are still used on this account.".format(
                    ", ".join(source_names)
                )
            else:
                error_message = "Can't save changes because media source {} is still used on this account.".format(
                    source_names[0]
                )
            raise utils.exc.ValidationError(errors={"allowed_media_sources": [str(error_message)]})

        if to_be_added or to_be_removed:
            changes = helpers.get_changes_for_sources(to_be_added, to_be_removed)
            account.allowed_sources.add(*list(to_be_added))
            account.allowed_sources.remove(*list(to_be_removed))
            account.write_history(
                changes, action_type=dash.constants.HistoryActionType.SETTINGS_CHANGE, user=request.user
            )

    @staticmethod
    def _handle_deals(request, account, data):
        errors = []
        new_deals = []

        for item in data:
            try:
                new_deals.append(restapi.access.get_direct_deal(request.user, item.get("id")))
                errors.append(None)
            except utils.exc.MissingDataError as err:
                errors.append({"id": [str(err)]})

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"deals": errors})

        new_deals_set = set(new_deals)

        deals = account.get_deals()
        deals_set = set(deals)

        to_be_removed = deals_set.difference(new_deals_set)
        to_be_added = new_deals_set.difference(deals_set)

        if to_be_removed or to_be_added:
            account.remove_deals(request, list(to_be_removed))
            account.add_deals(request, list(to_be_added))
