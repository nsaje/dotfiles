from django.db import models

import core.features.bcm
import core.models.helpers
import dash.constants

OEN_ACCOUNT_ID = 305
ZMS_TAG = "outbrain/sales/OutbrainSalesforce"


class AccountQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(models.Q(users__id=user.id) | models.Q(agency__users__id=user.id)).distinct()

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
                predicate = predicate | models.Q(id=OEN_ACCOUNT_ID)
            if dash.constants.Business.ZMS not in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=ZMS_TAG)
            return self.exclude(predicate)
        else:
            if dash.constants.Business.OEN in business_types:
                predicate = predicate | models.Q(id=OEN_ACCOUNT_ID)
            if dash.constants.Business.ZMS in business_types:
                predicate = predicate | models.Q(agency__entity_tags__name__icontains=ZMS_TAG)
            return self.filter(predicate)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)

    def filter_with_spend(self):
        return self.filter(
            pk__in=set(
                core.features.bcm.BudgetDailyStatement.objects.filter(budget__campaign__account_id__in=self)
                .filter(media_spend_nano__gt=0)
                .values_list("budget__campaign__account_id", flat=True)
            )
        )

    def all_use_bcm_v2(self):
        return all(self.values_list("uses_bcm_v2", flat=True))
