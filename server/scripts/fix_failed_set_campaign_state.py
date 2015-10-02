
from django.db import transaction

from dash import models as dm
from actionlog import models as am
from actionlog import constants as ac

import actionlog.api
import actionlog.zwei_actions

failed = am.ActionLog.objects.filter(state=ac.ActionState.FAILED, action=ac.Action.SET_CAMPAIGN_STATE)

# 1. for each failed actionlog check source state and compare it with needed state
# 2. if source state differs from our state --> create a new action based on our needs
# 3. abort all actionlogs

attrs = ('state', 'cpc_cc', 'daily_budget_cc')

actions = []
for fail in failed:
    ad_group_source = fail.ad_group_source

    adgs_settings = dm.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).latest()
    adgs_state = dm.AdGroupSourceState.objects.filter(ad_group_source=ad_group_source).latest()

    with transaction.atomic():

        fail.state = ac.ActionState.ABORTED
        fail.save()

        # find diff
        changes = {}
        for attr in attrs:
            settings_val = getattr(adgs_settings, attr)
            state_val = getattr(adgs_state, attr)

            if attr != attrs:
                changes[attr] = settings_val

        if changes:
            actions.extend(
                actionlog.api.set_ad_group_source_settings(changes, ad_group_source, request=None, order=None, send=False)
            )

if actions:
    actionlog.zwei_actions.send(actions)
