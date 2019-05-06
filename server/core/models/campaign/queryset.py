from django.db import models

import core.models


class CampaignQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(account__users__id=user.id) | models.Q(account__agency__users__id=user.id)
        ).distinct()

    def filter_by_sources(self, sources):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        return self.filter(adgroup__adgroupsource__source__in=sources).distinct()

    def filter_by_agencies(self, agencies):
        if not agencies:
            return self
        return self.filter(account__agency__in=agencies)

    def filter_by_account_types(self, account_types):
        if not account_types:
            return self
        return self.filter(account__settings__account_type__in=account_types)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)
