import django.core.exceptions
import django.db.utils
from django.db.models import F
from rest_framework import generics
from rest_framework.serializers import ValidationError

import core.models
import utils.exc
from utils import metrics_compat
from utils.rest_common import authentication

from .. import base
from . import constants
from . import exceptions
from . import serializers
from . import service


class CreateClientView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.SALESFORCE_SERVICE_NAME),)

    def put(self, request):
        serializer = serializers.ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            client = service.create_client(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="validation-error", client_type=None)
            raise ValidationError(err)
        except django.db.utils.IntegrityError:
            metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="name-error", client_type=None)
            raise ValidationError({"name": "Name is not unique for this account type."})
        except Exception as err:
            metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="server-error", client_type=None)
            raise err
        metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="ok", client_type=request.data["type"])
        return self.response_ok({"z1_account_id": client.get_salesforce_id(), "z1_data": client.name})


class CreateCreditLineView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.SALESFORCE_SERVICE_NAME),)

    def put(self, request):
        serializer = serializers.CreditLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cli = service.create_credit_line_item(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            metrics_compat.incr("serviceapi.salesforce.create_credit", 1, status="validation-error")
            raise ValidationError(err)
        except Exception as err:
            metrics_compat.incr("serviceapi.salesforce.create_credit", 1, status="server-error")
            raise err
        metrics_compat.incr("serviceapi.salesforce.create_credit", 1, status="ok")
        return self.response_ok({"z1_cli_id": cli.pk, "z1_data": cli.get_settings_dict()})


class AgencyAccountsView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.SALESFORCE_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AgencyAccountsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        accounts = service.get_agency_accounts(serializer.validated_data["z1_account_id"])

        return self.response_ok(
            [
                {"name": "#{} {}".format(account.pk, account.name), "z1_account_id": account.get_salesforce_id()}
                for account in accounts
            ]
        )


class CreditsListView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.SALESFORCE_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.Z1IdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credits = service.get_entity_credits(serializer.validated_data["z1_account_id"])
        if not credits:
            raise ValidationError("No credits found for this ID.")
        data = serializers.CreditsListSerializer(credits, many=True, context={"request": request})
        return self.response_ok(data.data, status=200)


# Outbrain Salesforce
class AgencyView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_agency = service.create_agency(request, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_agency", 1, status="ok")
            return self.response_ok(serializers.AgencySerializer(new_agency).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.create_agency", 1, status="validation-error")
            raise ValidationError(e)

    def put(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        serializer = serializers.AgencySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated_agency = service.update_agency(request, agency, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.modify_agency", 1, status="ok")
            return self.response_ok(serializers.AgencySerializer(updated_agency).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.modify_agency", 1, status="validation-error")
            raise ValidationError(e)

    def get(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        return self.response_ok(serializers.AgencySerializer(agency).data, status=200)


class AgenciesView(base.ServiceAPIBaseView, generics.ListAPIView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)
    serializer_class = serializers.AgencySerializer

    def get_queryset(self):
        queryset = core.models.Agency.objects.filter(is_externally_managed=True)
        date_range = serializers.DateRangeSerializer(data=self.request.query_params)
        date_range.is_valid(raise_exception=True)

        if not date_range.validated_data:
            raise exceptions.ListNoParametersProvided("Query parameters must be provided.")
        if date_range.validated_data.get("modified_dt_start"):
            queryset = queryset.filter(modified_dt__gte=date_range.validated_data["modified_dt_start"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("modified_dt_end"):
            queryset = queryset.filter(modified_dt__lte=date_range.validated_data["modified_dt_end"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("created_dt_start"):
            queryset = queryset.filter(created_dt__gte=date_range.validated_data["created_dt_start"])

        if date_range.validated_data.get("created_dt_end"):
            queryset = queryset.filter(created_dt__lte=date_range.validated_data["created_dt_end"])

        return set(queryset)


class AccountView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_account = service.create_account(request, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_account", 1, status="ok")
            return self.response_ok(serializers.AccountSerializer(new_account).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.create_account", 1, status="validation-error")
            raise ValidationError(e)

    def put(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        serializer = serializers.AccountSerializer(data=request.data, partial=True, context={"account_id": account_id})
        serializer.is_valid(raise_exception=True)
        try:
            updated_account = service.update_account(request, account, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.modify_account", 1, status="ok")
            return self.response_ok(serializers.AccountSerializer(updated_account).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.modify_account", 1, status="validation-error")
            raise ValidationError(e)

    def get(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        return self.response_ok(serializers.AccountSerializer(account).data, status=200)


class AccountsView(base.ServiceAPIBaseView, generics.ListAPIView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)
    serializer_class = serializers.AccountSerializer

    def get_queryset(self):
        queryset = core.models.Account.objects.filter(agency__is_externally_managed=True)
        date_range = serializers.DateRangeSerializer(data=self.request.query_params)
        date_range.is_valid(raise_exception=True)

        if not date_range.validated_data:
            raise exceptions.ListNoParametersProvided("Query parameters must be provided.")
        if date_range.validated_data.get("modified_dt_start"):
            queryset = queryset.filter(modified_dt__gte=date_range.validated_data["modified_dt_start"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("modified_dt_end"):
            queryset = queryset.filter(modified_dt__lte=date_range.validated_data["modified_dt_end"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("created_dt_start"):
            queryset = queryset.filter(created_dt__gte=date_range.validated_data["created_dt_start"])

        if date_range.validated_data.get("created_dt_end"):
            queryset = queryset.filter(created_dt__lte=date_range.validated_data["created_dt_end"])

        return set(queryset)


class AccountArchiveView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def get(self, request, account_id):
        account = core.models.Account.objects.get(id=account_id, agency__is_externally_managed=True)
        account.archive(request)
        metrics_compat.incr("archive_account", 1, status="ok")
        return self.response_ok(serializers.AccountSerializer(account).data, status=200)
