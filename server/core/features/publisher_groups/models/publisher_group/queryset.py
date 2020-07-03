from django.conf import settings
from django.db import models
from django.db.models import Count

import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models

ANNOTATION_QUALIFIED_PUBLISHER_GROUPS = set([16922])


class PublisherGroupQuerySet(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet
):
    def filter_by_implicit(self, implicit):
        return self.filter(implicit=implicit)

    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(account__users__id=user.id)
            | models.Q(account__agency__users__id=user.id)
            | models.Q(agency__users__id=user.id)
        ).distinct()

    def filter_by_account(self, account):
        if account.agency:
            return self.filter(models.Q(account=account) | models.Q(agency=account.agency))

        return self.filter(account=account)

    def filter_by_agency(self, agency):
        return self.filter(models.Q(agency=agency))

    def filter_by_active_candidate_adgroups(self):
        data = (
            core.models.AdGroup.objects.all()
            .filter_active_candidate()
            .values_list(
                "default_blacklist_id",
                "default_whitelist_id",
                "settings__whitelist_publisher_groups",
                "settings__blacklist_publisher_groups",
                "campaign__default_blacklist_id",
                "campaign__default_whitelist_id",
                "campaign__settings__whitelist_publisher_groups",
                "campaign__settings__blacklist_publisher_groups",
                "campaign__account__default_blacklist_id",
                "campaign__account__default_whitelist_id",
                "campaign__account__settings__whitelist_publisher_groups",
                "campaign__account__settings__blacklist_publisher_groups",
                "campaign__account__agency__default_blacklist_id",
                "campaign__account__agency__default_whitelist_id",
                "campaign__account__agency__settings__whitelist_publisher_groups",
                "campaign__account__agency__settings__blacklist_publisher_groups",
            )
        )

        ids = set()
        ids.add(settings.GLOBAL_BLACKLIST_ID)
        ids.update(ANNOTATION_QUALIFIED_PUBLISHER_GROUPS)

        self._all_ids_from_values_list_to_set(data, ids)

        return self.filter(id__in=ids)

    def search(self, search_expression):
        return self.filter(name__icontains=search_expression)

    def annotate_entities_count(self):
        return self.annotate(entities_count=Count("entries"))

    def _get_query_path_to_account(self) -> str:
        return "account"

    def _filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        query_set = super(PublisherGroupQuerySet, self)._filter_by_entity_permission(user, permission)
        query_set |= self.filter(
            models.Q(agency__entitypermission__user=user) & models.Q(agency__entitypermission__permission=permission)
        )
        return query_set

    def _all_ids_from_values_list_to_set(self, data, ids):
        for line in data:
            for item in line:
                if not item:
                    continue
                try:
                    for value in item:
                        if not value:
                            continue
                        ids.add(value)
                except TypeError:
                    ids.add(item)
