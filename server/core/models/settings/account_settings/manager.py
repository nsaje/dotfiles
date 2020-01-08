import core.common
import dash.constants

from . import model


class AccountSettingsManager(core.common.QuerySetManager):
    def get_default(self, request, account, name, agency=None):
        settings = model.AccountSettings(account=account, name=name)
        settings.default_account_manager = request.user

        if agency is not None:
            settings.default_sales_representative = agency.sales_representative
            settings.default_cs_representative = agency.cs_representative
            settings.ob_representative = agency.ob_representative
            settings.account_type = dash.constants.AccountType.ACTIVATED
            settings.auto_add_new_sources = not agency.entity_tags.filter(name__icontains="biz/NES").exists()

        return settings
