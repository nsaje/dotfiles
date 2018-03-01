from django.db import transaction

from dash import constants
import core.common

from . import model


EUR_AGENCIES = [196, 175]


class AccountManager(core.common.QuerySetManager):

    @transaction.atomic()
    def create(self, request, name, agency=None):
        if agency is not None:
            core.common.entity_limits.enforce(
                model.Account.objects.filter(agency=agency).exclude_archived(),
            )
        account = model.Account(name=name, agency=agency)
        if agency is not None:
            account.uses_bcm_v2 = agency.new_accounts_use_bcm_v2
        else:
            account.uses_bcm_v2 = True  # TODO: when all agencies are migrated, this can be moved into a db field default

        # FIXME(nsaje): remove when multicurrency finished
        if agency is not None and agency.id in EUR_AGENCIES:
            account.currency = constants.Currency.EUR

        account.save(request)
        account.write_history(
            'Created account',
            user=request.user,
            action_type=constants.HistoryActionType.CREATE)

        settings_updates = {}
        settings_updates['default_account_manager'] = request.user
        if agency is not None:
            settings_updates['default_sales_representative'] = agency.sales_representative
            settings_updates['default_cs_representative'] = agency.cs_representative
            settings_updates['account_type'] = constants.AccountType.ACTIVATED

        account.settings = core.entity.settings.AccountSettings(account=account)
        account.settings.update(request, **settings_updates)

        account.settings_id = account.settings.id
        account.save(request)

        if account.agency and account.agency.allowed_sources.count() > 0:  # FIXME(nsaje): rethink this
            account.allowed_sources.add(*agency.allowed_sources.all())
        else:
            account.allowed_sources.add(*core.source.Source.objects.filter(released=True, deprecated=False))

        return account
