import decimal

import django.forms

from dash import constants, retargeting_helper, validation_helpers, cpc_constraints
import utils.exc

LANDING_MODE_PREVENT_UPDATE = ['daily_budget_cc', 'state']


def validate_ad_group_source_updates(ad_group_source, updates, ad_group_settings, ad_group_source_settings):
    bcm_modifiers = ad_group_source.ad_group.campaign.get_bcm_modifiers()
    _validate_ad_group_source_cpc(ad_group_source, updates, bcm_modifiers)
    _validate_ad_group_source_daily_budget(ad_group_source, updates, bcm_modifiers)
    _validate_ad_group_source_state(ad_group_source, updates, ad_group_settings, ad_group_source_settings)


def _validate_ad_group_source_cpc(ad_group_source, updates, bcm_modifiers):
    if 'cpc_cc' in updates:
        assert isinstance(updates['cpc_cc'], decimal.Decimal)
        try:
            validation_helpers.validate_ad_group_source_cpc_cc(
                updates['cpc_cc'],
                ad_group_source,
                bcm_modifiers,
            )
            cpc_constraints.validate_cpc(
                updates['cpc_cc'],
                bcm_modifiers,
                ad_group=ad_group_source.ad_group,
                source=ad_group_source.source,
            )
        except django.forms.ValidationError as e:
            raise utils.exc.ValidationError(errors={
                'cpc_cc': [e.message],
            })


def _validate_ad_group_source_daily_budget(ad_group_source, updates, bcm_modifiers):
    if 'daily_budget_cc' in updates:
        assert isinstance(updates['daily_budget_cc'], decimal.Decimal)
        try:
            validation_helpers.validate_daily_budget_cc(
                updates['daily_budget_cc'],
                ad_group_source.source.source_type,
                bcm_modifiers,
            )
        except django.forms.ValidationError as e:
            raise utils.exc.ValidationError(errors={
                'daily_budget_cc': [e.message],
            })


def _validate_ad_group_source_state(ad_group_source, updates, ad_group_settings, ad_group_source_settings):
    from dash.views import helpers
    if 'state' in updates and updates['state'] == constants.AdGroupSettingsState.ACTIVE:
        if not retargeting_helper.can_add_source_with_retargeting(ad_group_source.source, ad_group_settings):
            raise utils.exc.ValidationError(errors={
                'state': 'Cannot enable media source that does not support'
                'retargeting on adgroup with retargeting enabled.'
            })
        elif not helpers.check_facebook_source(ad_group_source):
            raise utils.exc.ValidationError(errors={
                'state': 'Cannot enable Facebook media source that isn\'t connected to a Facebook page.',
            })
        elif not helpers.check_yahoo_min_cpc(ad_group_settings, ad_group_source, ad_group_source_settings):
            raise utils.exc.ValidationError(errors={
                'state': 'Cannot enable Yahoo media source with the current settings - CPC too low',
            })


def validate_ad_group_source_campaign_stop(ad_group_source, updates, campaign_settings, ad_group_settings, ad_group_source_settings):
    from automation import campaign_stop
    from dash.views import helpers

    if campaign_settings.landing_mode:
        for key in updates.keys():
            if key not in LANDING_MODE_PREVENT_UPDATE:
                continue
            raise utils.exc.ValidationError(errors={key: 'Not allowed'})
    elif campaign_settings.automatic_campaign_stop:
        if 'daily_budget_cc' in updates:
            new_daily_budget = decimal.Decimal(updates['daily_budget_cc'])
            max_daily_budget = campaign_stop.get_max_settable_source_budget(
                ad_group_source,
                ad_group_source.ad_group.campaign,
                ad_group_source_settings,
                ad_group_settings,
                campaign_settings
            )
            if max_daily_budget is not None and new_daily_budget > max_daily_budget:
                raise utils.exc.ValidationError(errors={
                    'daily_budget_cc': [
                        'Daily Spend Cap is too high. Maximum daily spend cap can be up to ${max_daily_budget}.'.format(
                            max_daily_budget=max_daily_budget
                        )
                    ]
                })

        if 'state' in updates:
            can_enable_media_source = campaign_stop.can_enable_media_source(
                ad_group_source, ad_group_source.ad_group.campaign, campaign_settings, ad_group_settings)
            if not can_enable_media_source:
                raise utils.exc.ValidationError(errors={
                    'state': ['Please add additional budget to your campaign to make changes.']
                })

            if updates['state'] == constants.AdGroupSourceSettingsState.ACTIVE:
                enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(
                    ad_group_settings,
                    [ad_group_source],
                )
                if not enabling_autopilot_sources_allowed:
                    raise utils.exc.ValidationError(errors={
                        'state': ['Please increase Autopilot Daily Spend Cap to enable this source.']
                    })
