"""
This module contains legacy code that computes the changes in ad group sources rows
after a setting on a particular source was updated. This code will have to be refactored
since it was initially written for a different use case - polling from client which
isn't done anymore.
"""

from core import source
from dash import constants, models
from dash.views import helpers


def get_updated_ad_group_sources_changes(user, last_change_dt, filtered_sources, ad_group_id_=None):
    ad_group = models.AdGroup.objects.get(id=ad_group_id_)
    ad_group_settings = ad_group.get_current_settings()
    ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
    ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)

    new_last_change_dt, changed_ad_group_sources = helpers.get_ad_group_sources_last_change_dt(
        ad_group_sources,
        ad_group_sources_settings,
        last_change_dt=last_change_dt
    )

    notifications = helpers.get_ad_group_sources_notifications(
        ad_group_sources,
        ad_group_settings,
        ad_group_sources_settings,
    )

    response = {
        'last_change': new_last_change_dt,
        'in_progress': any(n['in_progress'] for n in list(notifications.values()))
    }

    if new_last_change_dt is not None:
        settings_map = {
            s.ad_group_source_id: s for s in ad_group_sources_settings
        }

        rows = {}
        if ad_group_settings.b1_sources_group_enabled and (
                not last_change_dt or ad_group_settings.created_dt > last_change_dt):
            status = ad_group_settings.state
            if status == constants.AdGroupSettingsState.ACTIVE:
                status = ad_group_settings.b1_sources_group_state

            rows[source.AllRTBSource.id] = {
                'status_setting': ad_group_settings.b1_sources_group_state,
                'status': status,
                'bid_cpc': ad_group_settings.local_b1_sources_group_cpc_cc,
                'current_bid_cpc': ad_group_settings.local_b1_sources_group_cpc_cc,
                'daily_budget': ad_group_settings.local_b1_sources_group_daily_budget,
                'current_daily_budget': ad_group_settings.local_b1_sources_group_daily_budget,
            }
        for ad_group_source in changed_ad_group_sources:
            ags_setting = settings_map.get(ad_group_source.id)

            current_bid_cpc = None
            current_daily_budget = None
            status = None
            if ags_setting and ad_group_settings:
                current_bid_cpc = ags_setting.local_cpc_cc
                current_daily_budget = ags_setting.local_daily_budget_cc
                status = ad_group_settings.state
                if status == constants.AdGroupSettingsState.ACTIVE:
                    status = ags_setting.state

            status_setting = status
            if ags_setting and ags_setting.state:
                status_setting = ags_setting.state

            bid_cpc = current_bid_cpc
            daily_budget = current_daily_budget

            if ags_setting and ags_setting.local_cpc_cc:
                bid_cpc = ags_setting.local_cpc_cc
            if ags_setting and ags_setting.local_daily_budget_cc:
                daily_budget = ags_setting.local_daily_budget_cc

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
        daily_budget = _get_daily_budget(user, filtered_sources, ad_group_settings, ad_group_sources_settings)
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


def _get_daily_budget(user, filtered_sources, ad_group_settings, ad_group_sources_settings):
    # MVP for all-RTB-sources-as-one
    all_rtb_budget = 0
    include_rtb_sources = True
    if ad_group_settings.b1_sources_group_enabled:
        include_rtb_sources = False
        all_rtb_budget = 0
        if ad_group_settings.b1_sources_group_state == \
                constants.AdGroupSourceSettingsState.ACTIVE:
            all_rtb_budget = ad_group_settings.local_b1_sources_group_daily_budget

    daily_budget = _get_daily_budget_total(user, filtered_sources, ad_group_sources_settings, include_rtb_sources)
    if not include_rtb_sources:
        daily_budget = daily_budget + all_rtb_budget if daily_budget else all_rtb_budget

    return daily_budget


def _get_daily_budget_total(user, filtered_sources, ad_group_sources_settings, include_rtb_sources=True):
    if not filtered_sources:
        filtered_sources = []
    filtered_sources = [int(s) for s in filtered_sources]

    budgets = [s.local_daily_budget_cc for s in ad_group_sources_settings if
               s is not None and s.local_daily_budget_cc is not None and
               (not filtered_sources or s.ad_group_source.source_id in filtered_sources) and
               s.state == constants.AdGroupSourceSettingsState.ACTIVE and
               (include_rtb_sources or s.ad_group_source.source.source_type.type != constants.SourceType.B1)]

    if not budgets:
        return None

    return sum(budgets)
