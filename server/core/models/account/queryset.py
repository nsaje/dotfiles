from django.conf import settings
from django.db import models

import core.features.bcm
import core.models.helpers
import dash.constants
import zemauth.features.entity_permission.shortcuts
import zemauth.models

ZMS_TAG = "outbrain/sales/OutbrainSalesforce"
NAS_TAG = "biz/NES"
INTERNAL_TAG = "biz/internal"


class AccountQuerySet(zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet):
    def filter_by_sources(self, sources):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self
        return self.filter(campaign__adgroup__adgroupsource__source__id__in=sources).distinct()

    def filter_by_agencies(self, agencies):
        if not agencies:
            return self
        return self.filter(agency__in=agencies)

    def filter_by_account_types(self, account_types):
        if not account_types:
            return self
        return self.filter(settings__account_type__in=account_types)

    def filter_by_business(self, business_types):
        if not business_types:
            return self
        predicate = models.Q()
        if dash.constants.Business.Z1 in business_types:
            if dash.constants.Business.OEN not in business_types:
                predicate = predicate | models.Q(id=settings.HARDCODED_ACCOUNT_ID_OEN)
            if dash.constants.Business.ZMS not in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=ZMS_TAG)
            if dash.constants.Business.NAS not in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=NAS_TAG)
            if dash.constants.Business.INTERNAL not in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=INTERNAL_TAG)
            return self.exclude(predicate)
        else:
            if dash.constants.Business.OEN in business_types:
                predicate = predicate | models.Q(id=settings.HARDCODED_ACCOUNT_ID_OEN)
            if dash.constants.Business.ZMS in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=ZMS_TAG)
            if dash.constants.Business.NAS in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=NAS_TAG)
            if dash.constants.Business.INTERNAL in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=INTERNAL_TAG)
            return self.filter(predicate)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)

    def filter_with_spend(self):
        return self.filter(
            pk__in=set(
                core.features.bcm.BudgetDailyStatement.objects.filter(budget__campaign__account_id__in=self)
                .filter(base_media_spend_nano__gt=0)
                .values_list("budget__campaign__account_id", flat=True)
            )
        )

    def _get_query_path_to_account(self) -> str:
        return ""
