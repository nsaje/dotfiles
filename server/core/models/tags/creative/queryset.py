from django.db import models

import zemauth.features.entity_permission.shortcuts


class CreativeTagQuerySet(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet
):
    def filter_by_agency(self, agency):
        return self.filter(models.Q(agency=agency))

    def filter_by_agency_and_related_accounts(self, agency):
        return self.filter(models.Q(agency=agency) | models.Q(account__agency=agency))

    def filter_by_account(self, account):
        query_set = self.filter(models.Q(account=account))
        if account.agency is not None:
            query_set |= self.filter_by_agency(account.agency)
        return query_set

    def _get_query_path_to_account(self) -> str:
        return "account"

    def _filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        query_set = super(CreativeTagQuerySet, self)._filter_by_entity_permission(user, permission)
        query_set |= self.filter(
            models.Q(agency__entitypermission__user=user) & models.Q(agency__entitypermission__permission=permission)
        )
        return query_set
