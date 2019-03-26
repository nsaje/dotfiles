import logging

from django.db import transaction

import core.common
import core.features.yahoo_accounts
from dash import constants
from utils import exc
from utils import slack

from . import model

logger = logging.getLogger(__name__)


EUR_AGENCIES = [196, 175, 179, 201]


class AccountManager(core.common.BaseManager):
    @transaction.atomic()
    def create(self, request, name, agency=None, currency=None, **kwargs):
        if agency is not None:
            core.common.entity_limits.enforce(model.Account.objects.filter(agency=agency).exclude_archived())
        account = model.Account(name=name, agency=agency)
        if agency is not None:
            account.uses_bcm_v2 = agency.new_accounts_use_bcm_v2
        else:
            account.uses_bcm_v2 = (
                True
            )  # TODO: when all agencies are migrated, this can be moved into a db field default

        # FIXME(nsaje): remove when multicurrency finished
        if agency is not None and agency.id in EUR_AGENCIES:
            account.currency = constants.Currency.EUR
        else:
            account.currency = currency

        account.yahoo_account = core.features.yahoo_accounts.get_default_account()
        account.is_disabled = kwargs.get("is_disabled", False)
        account.salesforce_url = kwargs.get("salesforce_url", None)
        if account.is_disabled and not account.is_externally_managed:
            raise exc.ValidationError("Disabling Account is allowed only on externally managed agencies.")

        account.save(request)
        account.write_history("Created account", user=request.user, action_type=constants.HistoryActionType.CREATE)
        account.entity_tags.add(*kwargs.get("entity_tags", []))

        settings_updates = {}
        settings_updates["default_account_manager"] = request.user
        # TODO: Seamless source release: set auto adding to true only when agency not a NAS
        if agency is not None:
            settings_updates["default_sales_representative"] = agency.sales_representative
            settings_updates["default_cs_representative"] = agency.cs_representative
            settings_updates["ob_representative"] = agency.ob_representative
            settings_updates["account_type"] = constants.AccountType.ACTIVATED
            settings_updates["auto_add_new_sources"] = True

        account.settings = core.models.settings.AccountSettings(account=account)
        account.settings.update(request, **settings_updates)

        account.settings_id = account.settings.id
        account.save(request)

        if account.agency and account.agency.allowed_sources.count() > 0:  # FIXME(nsaje): rethink this
            account.allowed_sources.add(*agency.allowed_sources.all())
        else:
            account.allowed_sources.add(*core.models.Source.objects.filter(released=True, deprecated=False))

        if "New account" not in account.name:
            slack_msg = (
                "Account #<https://one.zemanta.com/v2/analytics/account/{id}|{id}> {name} was created"
                "{agency}.".format(
                    id=account.id,
                    name=account.name,
                    agency=" for agency {}".format(account.agency.name) if account.agency else "",
                )
            )
            try:
                slack.publish(text=slack_msg, channel=slack.CHANNEL_ZEM_FEED_NEW_ACCOUNTS)
            except Exception:
                logger.exception("Connection error with Slack.")
        return account
