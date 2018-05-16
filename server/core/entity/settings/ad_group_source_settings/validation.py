import decimal

import django.forms

from dash import constants, retargeting_helper, validation_helpers, cpc_constraints
import utils.exc

LANDING_MODE_PREVENT_UPDATE = ['daily_budget_cc', 'state']


class AdGroupSourceSettingsValidatorMixin(object):

    # TODO (multicurrency): Modify validation to work with multiple currencies
    def clean(self, new_settings):
        bcm_modifiers = self.ad_group_source.ad_group.campaign.get_bcm_modifiers()
        self._validate_ad_group_source_cpc(new_settings, bcm_modifiers)
        self._validate_ad_group_source_daily_budget(new_settings, bcm_modifiers)
        self._validate_ad_group_source_state(new_settings)

    def _validate_ad_group_source_cpc(self, new_settings, bcm_modifiers):
        if not new_settings.cpc_cc:
            return
        assert isinstance(new_settings.cpc_cc, decimal.Decimal)
        try:
            validation_helpers.validate_ad_group_source_cpc_cc(
                new_settings.cpc_cc,
                self.ad_group_source,
                bcm_modifiers,
            )
            cpc_constraints.validate_cpc(
                new_settings.cpc_cc,
                bcm_modifiers,
                ad_group=self.ad_group_source.ad_group,
                source=self.ad_group_source.source,
            )
        except django.forms.ValidationError as e:
            raise utils.exc.ValidationError(errors={
                'cpc_cc': [e.message],
            })

    def _validate_ad_group_source_daily_budget(self, new_settings, bcm_modifiers):
        if not new_settings.daily_budget_cc:
            return
        assert isinstance(new_settings.daily_budget_cc, decimal.Decimal)
        try:
            validation_helpers.validate_daily_budget_cc(
                new_settings.daily_budget_cc,
                self.ad_group_source.source.source_type,
                bcm_modifiers,
            )
        except django.forms.ValidationError as e:
            raise utils.exc.ValidationError(errors={
                'daily_budget_cc': [e.message],
            })

    def _validate_ad_group_source_state(self, new_settings):
        from dash.views import helpers
        if self.state != new_settings.state and new_settings.state == constants.AdGroupSettingsState.ACTIVE:
            ad_group_settings = self.ad_group_source.ad_group.settings
            if not retargeting_helper.can_add_source_with_retargeting(
                    self.ad_group_source.source,
                    self.ad_group_source.ad_group.settings
            ):
                raise utils.exc.ValidationError(errors={
                    'state': 'Cannot enable media source that does not support'
                    'retargeting on adgroup with retargeting enabled.'
                })
            elif not helpers.check_facebook_source(self.ad_group_source):
                raise utils.exc.ValidationError(errors={
                    'state': 'Cannot enable Facebook media source that isn\'t connected to a Facebook page.',
                })
            elif not helpers.check_yahoo_min_cpc(ad_group_settings, self.ad_group_source, self):
                raise utils.exc.ValidationError(errors={
                    'state': 'Cannot enable Yahoo media source with the current settings - CPC too low',
                })

    def validate_ad_group_source_campaign_stop(self, new_settings):
        from dash.views import helpers

        campaign = self.ad_group_source.ad_group.campaign
        changes = self.get_setting_changes(new_settings)
        if campaign.settings.landing_mode:
            for key in list(changes.keys()):
                if key not in LANDING_MODE_PREVENT_UPDATE:
                    continue
                raise utils.exc.ValidationError(errors={key: 'Not allowed'})
        elif campaign.settings.automatic_campaign_stop:
            if 'state' in changes:
                if new_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
                    enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(
                        self.ad_group_source.ad_group,
                        [self.ad_group_source],
                    )
                    if not enabling_autopilot_sources_allowed:
                        raise utils.exc.ValidationError(errors={
                            'state': ['Please increase Autopilot Daily Spend Cap to enable this source.']
                        })
