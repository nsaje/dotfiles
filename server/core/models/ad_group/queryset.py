import datetime

from django.db import models

import dash.constants
import utils.dates_helper
import zemauth.features.entity_permission.shortcuts
import zemauth.models


class AdGroupQuerySet(zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet):
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
        ).exclude_end_date_before_date(date)

    def filter_active_candidate(self, date=None):
        """
        This function checks if adgroup is active and current or if it has hight probability of being active soon.
            - Ad group is active now or start date is in the near future
            - Settings were modified recently
            - Is not past the end date
        """
        if not date:
            date = utils.dates_helper.local_today()

        tomorrow_dt = date + datetime.timedelta(hours=24)
        recent_dt = date - datetime.timedelta(hours=24)

        return self.filter(
            (
                models.Q(settings__state=dash.constants.AdGroupSettingsState.ACTIVE)
                & models.Q(settings__start_date__lte=tomorrow_dt)
            )
            | models.Q(settings__created_dt__gte=recent_dt)
        ).exclude_end_date_before_date(date)

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

    def compute_total_local_daily_cap(self):
        qs = self.filter_current_and_active().select_related("settings")
        adgroup_sources = dash.models.AdGroupSource.objects.filter(
            settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE, ad_group__in=qs
        ).values("settings__local_daily_budget_cc", "ad_group_id", "source__source_type__type")

        adgroup_map = {ad_group.id: ad_group for ad_group in qs}
        ret = 0

        ad_groups_with_active_b1_sources = set()
        for adgroup_source in adgroup_sources:
            adgroup_settings = adgroup_map[adgroup_source["ad_group_id"]].settings

            if (
                adgroup_settings.b1_sources_group_enabled
                and adgroup_source["source__source_type__type"] == dash.constants.SourceType.B1
            ):
                ad_groups_with_active_b1_sources.add(adgroup_source["ad_group_id"])
                continue

            ret += adgroup_source["settings__local_daily_budget_cc"] or 0

        for ad_group_id in ad_groups_with_active_b1_sources:
            ags = adgroup_map[ad_group_id].settings

            if ags.b1_sources_group_state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
                continue

            ret += ags.local_b1_sources_group_daily_budget or 0

        return ret

    def exclude_end_date_before_date(self, date=None):
        if not date:
            date = utils.dates_helper.local_today()
        return self.exclude(settings__end_date__isnull=False, settings__end_date__lt=date)

    def filter_running_and_has_budget(self):
        return (
            self.filter_allowed_to_run().filter_at_least_one_source_running().exclude_end_date_before_date().distinct()
        )

    def _get_query_path_to_account(self) -> str:
        return "campaign__account"
