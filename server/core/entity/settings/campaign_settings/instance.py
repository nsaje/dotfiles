from django.db import transaction

import dash.constants
import utils.email_helper

import dash.features.ga
import utils.redirector_helper
import utils.k1_helper


class CampaignSettingsMixin(object):

    @transaction.atomic
    def update(self, request, **kwargs):
        clean_updates = self._clean_updates(kwargs)
        changes = self.get_changes(clean_updates)

        super(CampaignSettingsMixin, self).update(request, **changes)
        self._update_campaign(kwargs)

        if changes:
            self._log_and_notify_changes(request, changes)
            self._handle_ga_setup_instructions(request, changes)
            self._propagate_settings(changes)

    def _clean_updates(cls, kwargs):
        cleaned_updates = {}
        for field, value in kwargs.items():
            if field in cls._settings_fields:
                cleaned_updates[field] = value
        return cleaned_updates

    def _update_campaign(self, changes):
        if 'name' in changes:
            self.campaign.name = changes['name']
            self.campaign.save()

    def _log_and_notify_changes(self, request, changes):
        if changes and request and request.user:
            changes_text = self.get_changes_text(changes, separator='\n')
            utils.email_helper.send_campaign_notification_email(self.campaign, request, changes_text)

    def _handle_ga_setup_instructions(self, request, changes):
        if ('ga_property_id' in changes and self.enable_ga_tracking and self.ga_property_id):
            try:
                is_readable = dash.features.ga.is_readable(self.ga_property_id)
            except Exception:
                is_readable = False
            if not is_readable and request and request.user:
                utils.email_helper.send_ga_setup_instructions(request.user)

    def _propagate_settings(self, changes):
        campaign_ad_groups = self.campaign.adgroup_set.all().select_related('settings', 'campaign__settings')

        any_tracking_changes = any(prop in changes for prop in
                                   ['enable_ga_tracking', 'enable_adobe_tracking', 'adobe_tracking_param'])
        if any_tracking_changes:
            for ad_group in campaign_ad_groups:
                utils.redirector_helper.insert_adgroup(ad_group)

        utils.k1_helper.update_ad_groups((ad_group.pk for ad_group in campaign_ad_groups),
                                         msg='CampaignSettings.update')
