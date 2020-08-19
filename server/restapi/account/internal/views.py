import rest_framework.permissions
from django.db import transaction

import core.features.deals
import core.models
import dash.constants
import dash.features.alerts
import restapi.account.v1.views
import restapi.common.helpers
import restapi.serializers.alert
import utils.exc
import zemauth.access
from zemauth.features.entity_permission.constants import Permission

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
        agencies = zemauth.access.get_agencies(request.user, Permission.WRITE)
        account = core.models.Account.objects.get_default(request, agencies.first())
        self._augment_account(request, account)
        extra_data = helpers.get_extra_data(request.user, account)
        return self.response_ok(
            data=self.serializer(account, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.READ, account_id)
        self._augment_account(request, account)
        extra_data = helpers.get_extra_data(request.user, account)
        return self.response_ok(
            data=self.serializer(account, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def alerts(self, request, account_id=None):
        qpe = restapi.serializers.alert.AlertQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            alerts = dash.features.alerts.get_account_alerts(request, account, **qpe.validated_data)
        else:
            alerts = dash.features.alerts.get_accounts_alerts(request, **qpe.validated_data)

        return self.response_ok(
            data=restapi.serializers.alert.AlertSerializer(alerts, many=True, context={"request": request}).data
        )

    def put(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data.get("settings", {})

        with transaction.atomic():
            settings = self._process_default_icon(settings, account, serializer.validated_data)
            self._update_account(request, account, settings)
            # self._validate_default_icon(account)
            if "allowed_media_sources" in serializer.validated_data.keys():
                self._handle_allowed_media_sources(
                    request, account, serializer.validated_data.get("allowed_media_sources", [])
                )
            if "deals" in serializer.validated_data.keys():
                self._handle_deals(request, account, serializer.validated_data.get("deals", []))

        self._augment_account(request, account)
        return self.response_ok(self.serializer(account, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        agency_id = serializer.validated_data.get("agency_id")
        agency = zemauth.access.get_agency(request.user, Permission.WRITE, agency_id) if agency_id is not None else None

        with transaction.atomic():
            new_account = core.models.Account.objects.create(
                request,
                name=serializer.validated_data.get("settings", {}).get("name"),
                agency=agency,
                currency=serializer.validated_data.get("currency"),
            )
            settings = serializer.validated_data.get("settings", {})
            settings = self._process_default_icon(settings, new_account, serializer.validated_data)
            self._update_account(request, new_account, settings)
            # self._validate_default_icon(new_account)
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
            account.allowed_media_sources = helpers.get_allowed_sources(account)
        account.deals = []
        if request.user.has_perm("zemauth.can_see_direct_deals_section"):
            account.deals = account.get_deals(request)

    @staticmethod
    def _validate_default_icon(account):
        if not account.is_archived() and not account.settings.default_icon:
            raise utils.exc.ValidationError("Default icon must be set before updating or creating a new account.")

    @staticmethod
    def _handle_allowed_media_sources(request, account, data):
        allowed_sources = helpers.get_allowed_sources(account)
        available_sources = restapi.common.helpers.get_available_sources(request.user, account.agency, account=account)

        new_allowed_sources = []
        data_dict = dict((x["id"], x) for x in data)
        for available_source in set(available_sources + allowed_sources):
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
            if item.get("id") is not None:
                try:
                    deal = core.features.deals.DirectDeal.objects.filter(pk=item.get("id")).first()
                    if not deal:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    if deal.agency_id and account.agency_id != deal.agency_id:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    if deal.account_id and account.id != deal.account_id:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    new_deals.append(deal)
                    errors.append(None)
                except utils.exc.MissingDataError as err:
                    errors.append({"id": [str(err)]})
            else:
                new_deal = core.features.deals.DirectDeal.objects.create(
                    request,
                    account=account,
                    source=item.get("source"),
                    deal_id=item.get("deal_id"),
                    name=item.get("name"),
                )
                new_deal.update(request, **item)
                new_deals.append(new_deal)
                errors.append(None)

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"deals": errors})

        new_deals_set = set(new_deals)

        deals = account.get_deals(request)
        deals_set = set(deals)

        to_be_removed = deals_set.difference(new_deals_set)
        to_be_added = new_deals_set.difference(deals_set)

        if to_be_removed or to_be_added:
            account.remove_deals(request, list(to_be_removed))
            account.add_deals(request, list(to_be_added))
