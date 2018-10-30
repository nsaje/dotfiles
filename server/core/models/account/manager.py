import logging

from django.db import transaction

import core.common
import core.features.yahoo_accounts
from dash import constants
from utils import slack

from . import model

logger = logging.getLogger(__name__)


EUR_AGENCIES = [196, 175, 179, 201]


class AccountManager(core.common.BaseManager):
    @transaction.atomic()
    def create(self, request, name, agency=None, currency=None):
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
        account.save(request)
        account.write_history("Created account", user=request.user, action_type=constants.HistoryActionType.CREATE)

        settings_updates = {}
        settings_updates["default_account_manager"] = request.user
        # TODO: Seamless source release: set auto adding to true when the feature is released
        if agency is not None:
            settings_updates["default_sales_representative"] = agency.sales_representative
            settings_updates["default_cs_representative"] = agency.cs_representative
            settings_updates["ob_representative"] = agency.ob_representative
            settings_updates["account_type"] = constants.AccountType.ACTIVATED

        account.settings = core.models.settings.AccountSettings(account=account)
        account.settings.update(request, **settings_updates)

        account.settings_id = account.settings.id
        account.save(request)

        if account.agency and account.agency.allowed_sources.count() > 0:  # FIXME(nsaje): rethink this
            account.allowed_sources.add(*agency.allowed_sources.all())
        else:
            account.allowed_sources.add(*core.models.Source.objects.filter(released=True, deprecated=False))
        slack_msg = (
            "New Account #{id} <https://one.zemanta.com/v2/credit/account/{id}|{account_name}> was created "
            "{agency}.".format(
                id=account.id,
                account_name=account.name,
                agency=" for account {}".format(account.agency.name) if account.agency else "",
            )
        )
        try:
            slack.publish(text=slack_msg, channel="client-development")
        except Exception:
            logger.exception("Connection error with Slack.")
        return account
