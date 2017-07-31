from decimal import Decimal

import core.bcm.credit_line_item
import dash.constants
import utils.converters
from . import constants

CLIENT_TYPE_OBJECT_MAP = {
    constants.CLIENT_TYPE_AGENCY: core.entity.agency.Agency,
    constants.CLIENT_TYPE_CLIENT_DIRECT: core.entity.account.Account
}

DEFAULT_ACCOUNT_TYPE = dash.constants.AccountType.TEST


def _get_client_lookup(z1_account_id):
    client_type, client_id = z1_account_id[0], int(z1_account_id[1:])
    if client_type == constants.ACCOUNT_ID_PREFIX_AGENCY:
        return {'agency_id': client_id}
    elif client_type == constants.ACCOUNT_ID_PREFIX_CLIENT_DIRECT:
        return {'account_id': client_id}
    return None


def create_credit_line_item(request, data):
    start_date = data['start_date']
    end_date = data['end_date']
    amount = int(data['amount_at_signing'])
    cli = dict(
        contract_id=str(data['salesforce_contract_id']),
        contract_number=str(data['contract_number']),

        license_fee=Decimal('0'),
        comment=data['description'],

        status=dash.constants.CreditLineItemStatus.SIGNED,
    )
    cli.update(**_get_client_lookup(data['z1_account_id']))

    if data['pf_schedule'] == constants.PF_SCHEDULE_FLAT_FEE:
        cli['flat_fee_start_date'] = start_date
        cli['flat_fee_end_date'] = end_date
        cli['flat_fee_cc'] = int(utils.converters.DOLAR_TO_CC * data['calc_variable_fee'])
    elif data['pf_schedule'] == constants.PF_SCHEDULE_UPFRONT:
        cli['flat_fee_start_date'] = start_date
        cli['flat_fee_end_date'] = start_date
        cli['flat_fee_cc'] = int(utils.converters.DOLAR_TO_CC * data['calc_variable_fee'])
    elif data['pf_schedule'] == constants.PF_SCHEDULE_PCT_FEE:
        cli['license_fee'] = data['pct_of_budget']

    return core.bcm.credit_line_item.CreditLineItem.objects.create(request, start_date, end_date, amount, **cli)


def create_client(request, data):
    client = CLIENT_TYPE_OBJECT_MAP[data['type']].objects.create(request, data['name'])
    if data['type'] == constants.CLIENT_TYPE_AGENCY:
        client.default_account_type = DEFAULT_ACCOUNT_TYPE
        client.save(request)
    elif data['type'] == constants.CLIENT_TYPE_CLIENT_DIRECT:
        new_settings = client.get_current_settings().copy_settings()
        new_settings.account_type = DEFAULT_ACCOUNT_TYPE
        new_settings.save(request)
    return client


def get_agency_accounts(z1_account_id):
    return core.entity.account.Account.objects.filter(**_get_client_lookup(z1_account_id)).order_by('name')
