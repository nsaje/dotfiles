import django.core.exceptions
import django.db.utils
from rest_framework.serializers import ValidationError

import core.models
from utils import metrics_compat
from utils.rest_common import authentication

from ... import base
from . import constants
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


class AgencyView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.SALESFORCE_SERVICE_NAME),)
    serializer = serializers.AgencySerializer

    def post(self, request):
        try:
            serializer = self.serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            created_agency = service.create_agency(request, serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="ok", client_type="agency")
            return self.response_ok(self.serializer(created_agency).data)
        except (django.core.exceptions.ValidationError, ValidationError) as err:
            metrics_compat.incr(
                "serviceapi.salesforce.create_client", 1, status="validation-error", client_type="agency"
            )
            raise ValidationError(err)
        except Exception as err:
            metrics_compat.incr("serviceapi.salesforce.create_client", 1, status="server-error", client_type="agency")
            raise err

    def get(self, request, agency_id):
        try:
            agency = core.models.Agency.objects.get(id=agency_id)
            metrics_compat.incr("serviceapi.salesforce.retrieve_agency", 1, status="ok", client_type="agency")
            return self.response_ok(self.serializer(agency).data)
        except django.core.exceptions.ObjectDoesNotExist:
            metrics_compat.incr(
                "serviceapi.salesforce.retrieve_agency", 1, status="validation-error", client_type="agency"
            )
            raise ValidationError({"entity": "Agency does not exists"})


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
