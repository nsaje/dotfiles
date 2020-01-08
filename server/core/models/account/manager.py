from django.db import transaction

import core.common
import core.features.yahoo_accounts
import core.models
import dash.features.custom_flags.constants
from dash import constants
from prodops import hacks
from utils import slack
from utils import zlogging

from . import exceptions
from . import model
from .validation import OUTBRAIN_SALESFORCE_SERVICE_USER

logger = zlogging.getLogger(__name__)


class AccountManager(core.common.BaseManager):
    @transaction.atomic()
    def create(self, request, name, agency=None, **kwargs):
        user = request.user if request else None
        if agency is not None:
            core.common.entity_limits.enforce(model.Account.objects.filter(agency=agency).exclude_archived())
        self._validate_externally_managed(user, agency)

        account = self._prepare(name=name, agency=agency, currency=kwargs.pop("currency", None))
        account.save(request)
        account.update(request, **kwargs)
        account.write_history("Created account", user=user, action_type=constants.HistoryActionType.CREATE)

        settings_updates = {}
        settings_updates["default_account_manager"] = user
        if agency is not None:
            settings_updates["default_sales_representative"] = agency.sales_representative
            settings_updates["default_cs_representative"] = agency.cs_representative
            settings_updates["ob_representative"] = agency.ob_representative
            settings_updates["account_type"] = constants.AccountType.ACTIVATED
            settings_updates["auto_add_new_sources"] = True
        self._set_sources(account, kwargs.get("allowed_sources"))

        account.settings = core.models.settings.AccountSettings(account=account, name=name)
        account.settings.update(request, **settings_updates)
        account.settings_id = account.settings.id
        account.save(request)
        hacks.apply_account_create_hack(request, account)

        self._log_new_account_to_slack(account)
        return account

    def get_default(self, request, agency=None):
        account = self._prepare(name="", agency=agency)
        account.settings = core.models.settings.AccountSettings.objects.get_default(
            request, account, account.name, agency=agency
        )
        return account

    def _prepare(self, name=None, agency=None, currency=None):
        account = model.Account(name=name, agency=agency)
        account.currency = currency
        if agency and agency.custom_flags:
            account.currency = (
                agency.custom_flags.get(dash.features.custom_flags.constants.DEFAULT_CURRENCY) or account.currency
            )
        if agency is not None:
            account.uses_bcm_v2 = agency.new_accounts_use_bcm_v2
            account.amplify_review = agency.amplify_review
        else:
            # TODO: when all agencies are migrated, this can be moved into a db field default
            account.uses_bcm_v2 = True
        account.yahoo_account = core.features.yahoo_accounts.get_default_account()
        return account

    def _validate_externally_managed(self, user, agency=None):
        if user and agency:
            if user.email != OUTBRAIN_SALESFORCE_SERVICE_USER and agency.is_externally_managed:
                raise exceptions.CreatingAccountNotAllowed(
                    "Creating accounts for an externally managed agency is prohibited."
                )

    def _log_new_account_to_slack(self, account):
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

    def _set_sources(self, account, allowed_sources):
        if allowed_sources:
            account.allowed_sources.set(allowed_sources)
        elif (
            not account.agency
            or not account.agency.available_sources.exists()
            and not account.agency.allowed_sources.exists()
        ):
            account.allowed_sources.add(*core.models.Source.objects.filter(released=True, deprecated=False))
        elif account.agency.available_sources.exists() and account.agency.allowed_sources.exists():
            account.allowed_sources.add(*account.agency.allowed_sources.all())
