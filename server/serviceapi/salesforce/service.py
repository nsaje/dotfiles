from decimal import Decimal

from rest_framework.serializers import ValidationError

import core.features.bcm.credit_line_item
import core.features.multicurrency
import core.models.account
import core.models.outbrain_account
import dash.constants
import utils.converters
import utils.exc
import zemauth.models

from . import constants

CLIENT_TYPE_OBJECT_MAP = {
    constants.CLIENT_TYPE_AGENCY: core.models.agency.Agency,
    constants.CLIENT_TYPE_CLIENT_DIRECT: core.models.account.Account,
}


def _get_client_lookup(z1_account_id):
    client_type, client_id = z1_account_id[0], int(z1_account_id[1:])
    if client_type == constants.ACCOUNT_ID_PREFIX_AGENCY:
        return {"agency_id": client_id}
    elif client_type == constants.ACCOUNT_ID_PREFIX_CLIENT_DIRECT:
        return {"account_id": client_id}
    else:
        raise ValidationError({"z1_account_id": "Invalid format"})
    return None


def create_credit_line_item(request, data):
    start_date = data["start_date"]
    end_date = data["end_date"]
    amount = int(data["amount_at_signing"])
    currency = data["currency"]
    cli = dict(
        contract_id=str(data["salesforce_contract_id"]),
        contract_number=str(data["contract_number"]),
        license_fee=Decimal("0"),
        comment=data["description"],
        status=dash.constants.CreditLineItemStatus.SIGNED,
        currency=currency,
    )
    cli.update(**_get_client_lookup(data["z1_account_id"]))

    if data["pf_schedule"] == constants.PF_SCHEDULE_FLAT_FEE:
        cli["flat_fee_start_date"] = start_date
        cli["flat_fee_end_date"] = end_date
        cli["flat_fee_cc"] = int(utils.converters.CURRENCY_TO_CC * data["calc_variable_fee"])
    elif data["pf_schedule"] == constants.PF_SCHEDULE_UPFRONT:
        cli["flat_fee_start_date"] = start_date
        cli["flat_fee_end_date"] = start_date
        cli["flat_fee_cc"] = int(utils.converters.CURRENCY_TO_CC * data["calc_variable_fee"])
    elif data["pf_schedule"] == constants.PF_SCHEDULE_PCT_FEE:
        cli["license_fee"] = data["pct_of_budget"]

    item = core.features.bcm.credit_line_item.CreditLineItem.objects.create(
        request, start_date, end_date, amount, **cli
    )

    return item


def create_client(request, data):
    cs = zemauth.models.User.objects.get(email=constants.DEFAULT_CS_REPRESENTATIVE)
    sales = zemauth.models.User.objects.get(email=constants.DEFAULT_SALES_REPRESENTATIVE)

    client = CLIENT_TYPE_OBJECT_MAP[data["type"]].objects.create(request, data["name"], currency=data["currency"])
    if data["type"] == constants.CLIENT_TYPE_AGENCY:
        client.default_account_type = constants.DEFAULT_ACCOUNT_TYPE
        client.sales_representative = sales
        client.cs_representative = cs
        client.entity_tags.add(*data.get("tags", []))
        client.save(request)
    elif data["type"] == constants.CLIENT_TYPE_CLIENT_DIRECT:
        client.settings.update(
            request,
            account_type=constants.DEFAULT_ACCOUNT_TYPE,
            default_sales_representative=sales,
            default_cs_representative=cs,
        )
        client.entity_tags.add(*data.get("tags", []))
        client.currency = data["currency"]
        client.save(request)
    return client


def get_agency_accounts(z1_account_id):
    return core.models.account.Account.objects.filter(**_get_client_lookup(z1_account_id)).order_by("name")


def get_entity_credits(z1_account_id):
    return core.features.bcm.credit_line_item.CreditLineItem.objects.filter(**_get_client_lookup(z1_account_id))


def _update_outbrain_account(marketer_id):
    if not marketer_id:
        return
    marketer = core.models.OutbrainAccount.objects.filter(marketer_id=marketer_id).first()
    if not marketer:
        core.models.OutbrainAccount.objects.create(marketer_id=marketer_id, used=True)
        return
    if marketer and not marketer.used:
        marketer.used = True
        marketer.save()


def create_agency(request, **params):
    params.update({"is_externally_managed": True})
    return core.models.Agency.objects.create(request, **params)


def update_agency(request, agency, **kwargs):
    agency.update(request, **kwargs)
    return agency


def create_account(request, **kwargs):
    agency = kwargs.pop("agency", None)
    if not agency:
        sales_rep_email = kwargs["settings"].get("default_sales_representative").email
        agency_id = constants.SALES_REP_AGENCY_MAPPING.get(sales_rep_email, constants.OUTBRAIN_UNKNOWN_AGENCY_ID)
        agency = core.models.Agency.objects.get(id=agency_id)

    if (
        "custom_attributes" in kwargs
        and kwargs["custom_attributes"].get("advertiser_account_type", "") == constants.VIDEO_ADVERTISER_TYPE
    ):
        agency = core.models.Agency.objects.get(id=constants.VIDEO_AGENCY_ID)

    settings_updates = kwargs.pop("settings", {})
    new_account = core.models.Account.objects.create(request, agency=agency, **kwargs)
    new_account.settings.update(request, account_type=dash.constants.AccountType.MANAGED, **settings_updates)

    _update_outbrain_account(kwargs.get("outbrain_marketer_id", None))

    return new_account


def update_account(request, account, **kwargs):
    settings_updates = kwargs.pop("settings", {})
    account.update(request, **kwargs)
    account.settings.update(request, **settings_updates)
    _update_outbrain_account(kwargs.get("outbrain_marketer_id", None))
    return account
