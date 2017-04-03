# -*- coding: utf-8 -*-

import core.common
import core.entity
import core.history
import core.source

from account_settings import AccountSettings


class AccountSettingsReadOnly(core.common.ReadOnlyModelMixin, AccountSettings):
    """
    Read-only proxy for account settings that disables unnecessary history snapshots because
    they are not needed we can guarantee no data will be modified.
    """

    SNAPSHOT_HISTORY = False

    class Meta(AccountSettings.Meta):
        app_label = 'dash'
        proxy = True

    class QuerySet(core.common.ReadOnlyQuerySet, AccountSettings.QuerySet):
        pass
