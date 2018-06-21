import django.core.exceptions
import django.db.utils
import influx
from rest_framework.serializers import ValidationError

from .. import base
from . import serializers, service
from utils.rest_common import authentication

SERVICE_NAME = 'salesforce'


class CreateClientView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            client = service.create_client(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            influx.incr('create_client', 1, status='validation-error')
            raise ValidationError(err)
        except django.db.utils.IntegrityError:
            influx.incr('create_client', 1, status='name-error')
            raise ValidationError(
                {'name': 'Name is not unique for this account type.'}
            )
        except Exception as err:
            influx.incr('create_client', 1, status='server-error')
            raise err
        influx.incr('create_client', 1, status='ok', client_type=request.data['type'])
        return self.response_ok({
            'z1_account_id': client.get_salesforce_id(),
            'z1_data': client.name,
        })


class CreateCreditLineView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.CreditLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cli = service.create_credit_line_item(request, serializer.validated_data)
        except django.core.exceptions.ValidationError as err:
            influx.incr('create_credit', 1, status='validation-error')
            raise ValidationError(err)
        except Exception as err:
            influx.incr('create_credit', 1, status='server-error')
            raise err
        influx.incr('create_credit', 1, status='ok')
        return self.response_ok({
            'z1_cli_id': cli.pk,
            'z1_data': cli.get_settings_dict()
        })


class AgencyAccountsView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def post(self, request):
        serializer = serializers.AgencyAccountsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        accounts = service.get_agency_accounts(serializer.validated_data['z1_account_id'])

        return self.response_ok([
            {
                'name': '#{} {}'.format(account.pk, account.name),
                'z1_account_id': account.get_salesforce_id(),
            } for account in accounts
        ])
