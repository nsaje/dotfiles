# -*- coding: utf-8 -*-

import core.entity.settings


class CopySettingsMixin(object):

    def copy_settings(self):
        new_settings = type(self)()

        for name in self._settings_fields:
            t = type(new_settings)
            if hasattr(t, name) and isinstance(getattr(t, name), property):
                # NOTE: properties can't be set, skip them
                continue
            setattr(new_settings, name, getattr(self, name))

        if type(self) == core.entity.settings.AgencySettings:
            new_settings.agency = self.agency
            new_settings.snapshot(previous=self)
        if type(self) == core.entity.settings.AccountSettings:
            new_settings.account = self.account
            new_settings.snapshot(previous=self)
        elif type(self) == core.entity.settings.CampaignSettings:
            new_settings.campaign = self.campaign
            new_settings.snapshot(previous=self)
        elif type(self) == core.entity.settings.AdGroupSettings:
            new_settings.ad_group = self.ad_group
            new_settings.snapshot(previous=self)
        elif type(self) == core.entity.settings.AdGroupSourceSettings:
            new_settings.ad_group_source = self.ad_group_source
            new_settings.snapshot(previous=self)

        return new_settings
