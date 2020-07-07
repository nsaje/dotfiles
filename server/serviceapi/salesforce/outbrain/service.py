import core.features.bcm.credit_line_item
import core.features.multicurrency
import core.models.account
import core.models.outbrain_account
import dash.constants

from . import constants


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
