from rest_framework import serializers

from .. import base, authentication

import dash.constants
import core.entity.account
import core.entity.agency
import core.bcm.credit_line_item

SERVICE_NAME = 'salesforce-test'

ACCOUNT_ID_PREFIX_AGENCY = 'a'
ACCOUNT_ID_PREFIX_CLIENT_DIRECT = 'b'

CLIENT_TYPE_AGENCY = 'agency'
CLIENT_TYPE_CLIENT_DIRECT = 'brand'

PF_SCHEDULE_FLAT_FEE = 'flat'
PF_SCHEDULE_PCT_FEE = 'pct'


class ClientSerializer(serializers.Serializer):
    salesforce_account_id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.ChoiceField([CLIENT_TYPE_AGENCY, CLIENT_TYPE_CLIENT_DIRECT])


class CreateClientView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = None
        prefix = ''
        if serializer.validated_data['type'] == CLIENT_TYPE_AGENCY:
            obj = core.entity.agency.Agency()
            prefix = ACCOUNT_ID_PREFIX_AGENCY
        elif serializer.validated_data['type'] == CLIENT_TYPE_CLIENT_DIRECT:
            obj = core.entity.account.Account()
            prefix = ACCOUNT_ID_PREFIX_CLIENT_DIRECT
        obj.name = serializer.validated_data['name']

        # TODO: store the data

        return self.response_ok({
            'z1_account_id': '{}{}'.format(prefix, obj.pk),
            'z1_data': obj.get_long_name(),
        })


class CreditLineSerializer(serializers.Serializer):
    salesforce_contract_id = serializers.CharField()
    salesforce_account_id = serializers.CharField()
    z1_account_id = serializers.CharField()
    contract_number = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    description = serializers.CharField()
    pf_schedule = serializers.ChoiceField([PF_SCHEDULE_FLAT_FEE, PF_SCHEDULE_PCT_FEE])
    amount_at_signing = serializers.DecimalField(max_digits=8, decimal_places=2)
    billing_contract = serializers.CharField()


class CreateCreditLineView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_oauth_authentication(SERVICE_NAME),
    )

    def put(self, request):
        serializer = CreditLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cli = core.bcm.credit_line_item.CreditLineItem(
            contract_id=serializer.validated_data['salesforce_contract_id'],
            part_id=serializer.validated_data['contract_number'],

            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            amount=serializer.validated_data['amount_at_signing'],
            comment=serializer.validated_data['description'],

            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=request.user,
        )
        client_id = int(serializer.validated_data['z1_account_id'][1:])
        if serializer.validated_data['z1_account_id'][0] == ACCOUNT_ID_PREFIX_AGENCY:
            cli.agency_id = client_id
        elif serializer.validated_data['z1_account_id'][0] == ACCOUNT_ID_PREFIX_CLIENT_DIRECT:
            cli.account_id = client_id
        if serializer.validated_data['pf_schedule'] == PF_SCHEDULE_FLAT_FEE:
            cli.flat_fee_start_date = cli.start_date
            cli.flat_fee_end_date = cli.end_date
            cli.flat_fee_cc = 0  # TODO: missing
        if serializer.validated_data['pf_schedule'] == PF_SCHEDULE_PCT_FEE:
            cli.license_fee = 0  # TODO: missing

        # TODO: store the data

        return self.response_ok({
            'z1_cli_id': cli.pk,
            'z1_data': cli.get_settings_dict()
        })
