
from django.db import transaction

from dash import models as dm
from dash import constants
from actionlog import models as am
from actionlog import constants as ac

import actionlog.api
import actionlog.zwei_actions

failed = am.ActionLog.objects.filter(state=ac.ActionState.FAILED, action=ac.Action.SET_CAMPAIGN_STATE)

# 1. for each failed actionlog check source state and compare it with needed state
# 2. if source state differs from our state --> create a new action based on our needs
# 3. abort all actionlogs

actions = []
for fail in failed:
    ad_group_source = fail.ad_group_source

    adgs_settings = dm.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).latest()
    adgs_state = dm.AdGroupSourceState.objects.filter(ad_group_source=ad_group_source).latest()

    ag_settings = ad_group_source.ad_group.get_current_settings()

    with transaction.atomic():

        fail.state = ac.ActionState.ABORTED
        fail.save()

        # find diff
        changes = {}
        for attr in ('cpc_cc', 'daily_budget_cc'):
            settings_val = getattr(adgs_settings, attr)
            state_val = getattr(adgs_state, attr)

            if settings_val != state_val:
                changes[attr] = settings_val

        if ag_settings == constants.AdGroupSettingsState.ACTIVE:
            if adgs_settings.state != adgs_state.state:
                changes['state'] = adgs_settings.state
        elif adgs_state.state == constants.AdGroupSourceSettingsState.ACTIVE:
            changes['state'] = constants.AdGroupSourceSettingsState.INACTIVE

        if changes:
            actions.extend(
                actionlog.api.set_ad_group_source_settings(
                    changes, ad_group_source, request=None, order=None, send=False)
            )

if actions:
    actionlog.zwei_actions.send(actions)
