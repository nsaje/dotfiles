"""
This module contains legacy code that computes the changes in ad group sources rows
after a setting on a particular source was updated. This code will have to be refactored
since it was initially written for a different use case - polling from client which
isn't done anymore.
"""

from dash import constants, models
from dash.views import helpers


def get_updated_ad_group_sources_changes(user, last_change_dt, filtered_sources, ad_group_id_=None):
    ad_group = models.AdGroup.objects.get(id=ad_group_id_)
    ad_group_settings = ad_group.get_current_settings()
    ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
    ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)
    ad_group_sources_states = helpers.get_ad_group_sources_states(ad_group_sources)

    new_last_change_dt, changed_ad_group_sources = helpers.get_ad_group_sources_last_change_dt(
        ad_group_sources,
        ad_group_sources_settings,
        ad_group_sources_states,
        last_change_dt=last_change_dt
    )

    notifications = helpers.get_ad_group_sources_notifications(
        ad_group_sources,
        ad_group_settings,
        ad_group_sources_settings,
        ad_group_sources_states
    )

    response = {
        'last_change': new_last_change_dt,
        'in_progress': any(n['in_progress'] for n in notifications.values())
    }

    if new_last_change_dt is not None:
        states = ad_group_sources_states
        settings = ad_group_sources_settings

        rows = {}
        for ad_group_source in changed_ad_group_sources:
            source_states = [s for s in states if s.ad_group_source.id == ad_group_source.id]
            source_settings = [s for s in settings if s.ad_group_source.id == ad_group_source.id]

            state = source_states[0] if len(source_states) else None
            setting = source_settings[0] if len(source_settings) else None

            status = state.state if state is not None else None
            status_setting = status
            if ad_group_source.source.can_update_state() and\
               setting is not None and\
               setting.state is not None:
                status_setting = setting.state

            current_daily_budget = state.daily_budget_cc if state is not None else None
            daily_budget = current_daily_budget
            if (ad_group_source.source.can_update_daily_budget_automatic() or
                    ad_group_source.source.can_update_daily_budget_manual()) and\
                    setting is not None and\
                    setting.daily_budget_cc is not None:
                daily_budget = setting.daily_budget_cc

            current_bid_cpc = state.cpc_cc if state is not None else None
            bid_cpc = current_bid_cpc
            if ad_group_source.source.can_update_cpc() and\
               setting is not None and\
               setting.cpc_cc is not None:
                bid_cpc = setting.cpc_cc

            rows[ad_group_source.source_id] = {
                'status_setting': status_setting,
                'status': status,
                'bid_cpc': bid_cpc,
                'current_bid_cpc': current_bid_cpc,
                'daily_budget': daily_budget,
                'current_daily_budget': current_daily_budget,
            }

            if ad_group_source.source.source_type.type == constants.SourceType.B1:
                _update_rtb_source_row(ad_group_settings,
                                       ad_group_source, rows, notifications)

        response['rows'] = rows

        daily_budget = _get_daily_budget(ad_group_settings, ad_group_sources_states)
        response['totals'] = {
            'daily_budget': daily_budget,
            'current_daily_budget': daily_budget,
        }

        response['notifications'] = notifications

    return response


def _update_rtb_source_row(ad_group_settings, ad_group_source, rows, notifications):
    # MVP for all-RTB-sources-as-one
    source_id = ad_group_source.source_id
    row = rows[ad_group_source.source_id]

    if ad_group_settings.b1_sources_group_enabled:
        del row['daily_budget']
        del row['current_daily_budget']

        if ad_group_settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.INACTIVE \
                and row['status'] == constants.AdGroupSourceSettingsState.ACTIVE:
            row['status'] = constants.AdGroupSourceSettingsState.INACTIVE
            notifications[source_id] = {
                'message': 'This media source is enabled but will not run until you enable RTB Sources.',
                'important': True,
            }


def _get_daily_budget(ad_group_settings, ad_group_sources_states):
    # MVP for all-RTB-sources-as-one
    all_rtb_budget = 0
    include_rtb_sources = True
    if ad_group_settings.b1_sources_group_enabled:
        include_rtb_sources = False
        all_rtb_budget = 0
        if ad_group_settings.b1_sources_group_state == \
                constants.AdGroupSourceSettingsState.ACTIVE:
            all_rtb_budget = ad_group_settings.b1_sources_group_daily_budget

    daily_budget = _get_daily_budget_total(ad_group_sources_states, include_rtb_sources)
    if not include_rtb_sources:
        daily_budget = daily_budget + all_rtb_budget if daily_budget else all_rtb_budget

    return daily_budget


def _get_daily_budget_total(states, include_rtb_sources=True):
    budgets = [s.daily_budget_cc for s in states if
               s is not None and s.daily_budget_cc is not None and
               s.state == constants.AdGroupSourceSettingsState.ACTIVE and
               (include_rtb_sources or s.ad_group_source.source.source_type.type != constants.SourceType.B1)
               ]

    if not budgets:
        return None

    return sum(budgets)
