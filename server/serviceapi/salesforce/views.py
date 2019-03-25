import django.core.exceptions
import django.db.utils
import influx
from rest_framework.serializers import ValidationError

import core.models
from utils.rest_common import authentication

from . import serializers
from . import service
from .. import base

SALESFORCE_SERVICE_NAME = "salesforce"
OUTBRAIN_SERVICE_NAME = "outbrain-salesforce"


class CreateClientView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SALESFORCE_SERVICE_NAME),
        authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            client = service.create_client(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            influx.incr("create_client", 1, status="validation-error")
            raise ValidationError(err)
        except django.db.utils.IntegrityError:
            influx.incr("create_client", 1, status="name-error")
            raise ValidationError({"name": "Name is not unique for this account type."})
        except Exception as err:
            influx.incr("create_client", 1, status="server-error")
            raise err
        influx.incr("create_client", 1, status="ok", client_type=request.data["type"])
        return self.response_ok({"z1_account_id": client.get_salesforce_id(), "z1_data": client.name})


class CreateCreditLineView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SALESFORCE_SERVICE_NAME),
        authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.CreditLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cli = service.create_credit_line_item(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            influx.incr("create_credit", 1, status="validation-error")
            raise ValidationError(err)
        except Exception as err:
            influx.incr("create_credit", 1, status="server-error")
            raise err
        influx.incr("create_credit", 1, status="ok")
        return self.response_ok({"z1_cli_id": cli.pk, "z1_data": cli.get_settings_dict()})


class AgencyAccountsView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SALESFORCE_SERVICE_NAME),
        authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),
    )

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
    authentication_classes = (
        authentication.gen_oauth_authentication(SALESFORCE_SERVICE_NAME),
        authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),
    )

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
    authentication_classes = (authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_agency = service.create_agency(request, **serializer.validated_data)
        return self.response_ok(
            {
                "id": new_agency.id,
                "status": new_agency.is_disabled,
                "name": new_agency.name,
                "tags": [str(tag) for tag in new_agency.entity_tags.all()],
            },
            status=200,
        )

    def put(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        serializer = serializers.AgencySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_agency = service.update_agency(request, agency, **serializer.validated_data)
        return self.response_ok(
            {
                "id": updated_agency.id,
                "status": updated_agency.is_disabled,
                "name": updated_agency.name,
                "tags": [str(tag) for tag in updated_agency.entity_tags.all()],
            },
            status=200,
        )

    def get(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        return self.response_ok(
            {
                "id": agency.id,
                "name": agency.name,
                "status": agency.is_disabled,
                "tags": [str(tag) for tag in agency.entity_tags.all()],
            },
            status=200,
        )


class AccountView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_account = service.create_account(request, **serializer.validated_data)
        return self.response_ok(
            {
                "id": new_account.id,
                "agency_id": new_account.agency.id,
                "status": new_account.is_disabled,
                "name": new_account.name,
                "salesforce_url": new_account.salesforce_url,
                "currency": new_account.currency,
                "sales_representative": new_account.settings.default_sales_representative.email
                if new_account.settings.default_sales_representative
                else None,
                "account_manager": new_account.settings.default_account_manager.email
                if new_account.settings.default_account_manager
                else None,
                "tags": [str(tag) for tag in new_account.entity_tags.all()],
            },
            status=200,
        )

    def put(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        serializer = serializers.AccountSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_account = service.update_account(request, account, **serializer.validated_data)
        return self.response_ok(
            {
                "id": updated_account.id,
                "agency_id": updated_account.agency.id,
                "status": updated_account.is_disabled,
                "name": updated_account.name,
                "salesforce_url": updated_account.salesforce_url,
                "currency": updated_account.currency,
                "sales_representative": updated_account.settings.default_sales_representative.email
                if updated_account.settings.default_sales_representative
                else None,
                "account_manager": updated_account.settings.default_account_manager.email
                if updated_account.settings.default_account_manager
                else None,
                "tags": [str(tag) for tag in updated_account.entity_tags.all()],
            },
            status=200,
        )

    def get(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        return self.response_ok(
            {
                "id": account.id,
                "agency_id": account.agency.id,
                "status": account.is_disabled,
                "name": account.name,
                "salesforce_url": account.salesforce_url,
                "currency": account.currency,
                "sales_representative": account.settings.default_sales_representative.email
                if account.settings.default_sales_representative
                else None,
                "account_manager": account.settings.default_account_manager.email
                if account.settings.default_account_manager
                else None,
                "tags": [str(tag) for tag in account.entity_tags.all()],
            },
            status=200,
        )
