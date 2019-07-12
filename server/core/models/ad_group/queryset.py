from django.db import models

import dash.constants
import utils.dates_helper


class AdGroupQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(campaign__account__users__id=user.id) | models.Q(campaign__account__agency__users__id=user.id)
        ).distinct()

    def filter_by_agencies(self, agencies):
        if not agencies:
            return self
        return self.filter(campaign__account__agency__in=agencies)

    def filter_by_account_types(self, account_types):
        if not account_types:
            return self
        return self.filter(campaign__account__settings__account_type__in=account_types)

    def filter_by_sources(self, sources):
        # FIXME:circular dependency
        import core.models.settings

        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        return self.filter(adgroupsource__source__in=sources).distinct()

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)

    def exclude_display(self, show_display=False):
        if show_display:
            return self
        return self.exclude(campaign__type=dash.constants.CampaignType.DISPLAY)

    def filter_current_and_active(self, date=None):
        """
        This function checks if adgroup is active and current on arbitrary number of adgroups
        with a fixed amount of queries.
        An adgroup is running if:
            - it was set as active(adgroupsettings)
            - current date is between start and stop(flight time)
        """
        if not date:
            date = utils.dates_helper.local_today()
        return self.filter(
            settings__state=dash.constants.AdGroupSettingsState.ACTIVE, settings__start_date__lte=date
        ).exclude(settings__end_date__isnull=False, settings__end_date__lt=date)

    def filter_active(self):
        """
        Returns only ad groups that have settings set to active.
        """
        return self.filter(settings__state=dash.constants.AdGroupSettingsState.ACTIVE)

    def filter_running(self, date=None):
        """
        Return only running ad groups.
        """
        return (
            self.filter_current_and_active(date=date)
            .filter_at_least_one_source_running()
            .filter_allowed_to_run()
            .distinct()
        )

    def filter_allowed_to_run(self):
        # FIXME:circular dependency
        from automation.campaignstop import constants as campaignstop_constants

        return self.filter(
            models.Q(
                campaign__real_time_campaign_stop=True,
                campaign__campaignstopstate__state=campaignstop_constants.CampaignStopState.ACTIVE,
            )
            | models.Q(campaign__real_time_campaign_stop=False)
        )

    def filter_at_least_one_source_running(self):
        return self.filter(
            adgroupsource__settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            settings__archived=False,
            campaign__settings__archived=False,
        )
