from .. import base, authentication
from . import serializers, service

SERVICE_NAME = 'salesforce-test'


class CreateClientView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = service.create_client(request, serializer.validated_data)

        return self.response_ok({
            'z1_account_id': client.get_salesforce_id(),
            'z1_data': client.get_long_name(),
        })


class CreateCreditLineView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = serializers.CreditLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cli = service.create_credit_line_item(request, serializer.validated_data)

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
                'name': u'#{} {}'.format(account.pk, account.name),
                'z1_account_id': account.get_salesforce_id(),
            } for account in accounts
        ])
