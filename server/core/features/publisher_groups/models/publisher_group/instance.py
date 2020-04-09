import core.models
from dash import constants


class PublisherGroupMixin(object):
    def save(self, request, *args, **kwargs):
        if request and request.user:
            self.modified_by = request.user
        self.full_clean()
        super().save(*args, **kwargs)

    def write_history(self, changes_text, changes, action_type, user=None, system_user=None):

        if not changes and not changes_text:
            return None

        account = self.account
        agency = self.agency
        level = constants.HistoryLevel.ACCOUNT if account else constants.HistoryLevel.AGENCY

        return core.features.history.History.objects.create(
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=changes,
            changes_text=changes_text or "",
            level=level,
            action_type=action_type,
        )

    def can_delete(self):
        # Check if any of the ad group, campaign and account settings of the corresponding account/agency reference the publisher group
        if self.agency:
            ad_groups_settings = core.models.settings.AdGroupSettings.objects.filter(
                ad_group__campaign__account__agency=self.agency
            )
            campaigns_settings = core.models.settings.CampaignSettings.objects.filter(
                campaign__account__agency=self.agency
            )
            accounts_settings = core.models.settings.AccountSettings.objects.filter(account__agency=self.agency)
        else:
            ad_groups_settings = core.models.settings.AdGroupSettings.objects.filter(
                ad_group__campaign__account=self.account
            )
            campaigns_settings = core.models.settings.CampaignSettings.objects.filter(campaign__account=self.account)
            accounts_settings = core.models.settings.AccountSettings.objects.filter(account=self.account)

        return not (
            self._is_publisher_group_in_use(ad_groups_settings)
            or self._is_publisher_group_in_use(campaigns_settings)
            or self._is_publisher_group_in_use(accounts_settings)
        )

    def _is_publisher_group_in_use(self, settings_queryset):
        # use `only` instead of `values` so that JSON fields get converted to arrays
        settings = settings_queryset.group_current_settings().only(
            "whitelist_publisher_groups", "blacklist_publisher_groups"
        )

        # flatten the list a bit (1 level still remains)
        publisher_groups = [x.whitelist_publisher_groups + x.blacklist_publisher_groups for x in settings]
        return any(self.id in x for x in publisher_groups)
