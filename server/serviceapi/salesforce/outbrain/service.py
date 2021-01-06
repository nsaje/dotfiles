from django.contrib.auth import models as auth_models

import core.features.bcm.credit_line_item
import core.features.multicurrency
import core.models.account
import core.models.outbrain_account
import dash.constants
import zemauth.features.entity_permission
import zemauth.models

from . import constants

ACCOUNT_PERMISSIONS = [
    zemauth.features.entity_permission.Permission.READ,
    zemauth.features.entity_permission.Permission.WRITE,
    zemauth.features.entity_permission.Permission.BUDGET,
    zemauth.features.entity_permission.Permission.AGENCY_SPEND_MARGIN,
    zemauth.features.entity_permission.Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    zemauth.features.entity_permission.Permission.BASE_COSTS_SERVICE_FEE,
]


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
    sales_rep = kwargs["settings"].get("default_sales_representative")
    account_manager = kwargs["settings"].get("default_account_manager")

    agency = kwargs.pop("agency", None)
    if not agency:
        agency_id = constants.SALES_OFFICE_AGENCY_MAPPING.get(sales_rep.sales_office)
        if not agency_id:
            agency_id = constants.SALES_REP_AGENCY_MAPPING.get(sales_rep.email, constants.OUTBRAIN_UNKNOWN_AGENCY_ID)
            # TODO jholas remove above line and uncomment exception when out if hybrid phase
            # raise utils.exc.ValidationError("Agency for this sales office doesn't exist")
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

    zemauth.features.entity_permission.add_entity_permissions(sales_rep, None, new_account, ACCOUNT_PERMISSIONS)

    if account_manager:
        zemauth.features.entity_permission.add_entity_permissions(
            account_manager, None, new_account, ACCOUNT_PERMISSIONS
        )

    return new_account


def update_account(request, account, **kwargs):
    settings_updates = kwargs.pop("settings", {})
    account.update(request, **kwargs)
    account.settings.update(request, **settings_updates)
    _update_outbrain_account(kwargs.get("outbrain_marketer_id", None))
    return account


def create_user(**kwargs):
    kwargs.update({"is_externally_managed": True, "status": zemauth.models.user.constants.Status.ACTIVE})
    user = zemauth.models.User.objects.create_user(**kwargs)
    perm = auth_models.Permission.objects.get(codename="this_is_public_group")
    group = auth_models.Group.objects.filter(permissions=perm).first()
    if group is not None:
        group.user_set.add(user)
    return user


def update_user(user, **kwargs):
    user.update(**kwargs)
    return user
