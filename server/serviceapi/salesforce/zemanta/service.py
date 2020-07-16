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


def create_agency(request, validated_data):
    cs_representative = zemauth.models.User.objects.get(email=constants.DEFAULT_CS_REPRESENTATIVE)
    sales_representative = zemauth.models.User.objects.get(email=constants.DEFAULT_SALES_REPRESENTATIVE)
    entity_tags = validated_data.pop("entity_tags", [])

    client_type = validated_data.pop("client_type", None)
    if client_type:
        entity_tags.append(constants.ENTITY_TAGS_PREFIX + client_type)

    client_size = validated_data.pop("client_size", None)
    if client_size:
        entity_tags.append(constants.ENTITY_TAGS_PREFIX + client_size)

    region = validated_data.pop("region", None)
    if region:
        entity_tags.append(constants.ENTITY_TAGS_PREFIX + region.replace("-", "/"))
        if region != constants.ENTITY_TAGS_US:
            entity_tags.append(constants.ENTITY_TAGS_PREFIX + constants.ENTITY_TAGS_INTL)

    return core.models.Agency.objects.create(
        request,
        cs_representative=cs_representative,
        sales_representative=sales_representative,
        entity_tags=entity_tags,
        **validated_data,
    )
