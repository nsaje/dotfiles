from django.contrib.auth import models as auth_models
from django.db import models
from django.db import transaction

import core.models

SUPERUSER_EXCLUDED_PERMISSIONS = (
    "disable_public_rcs",
    "disable_public_newscorp",
    "disable_budget_management",
    "can_see_projections",
)


class UserMixin(object):
    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def __str__(self):
        return self.email

    def get_all_permissions_with_access_levels(self):
        if not self.is_active or self.is_anonymous:
            return {}

        perm_cache_name = "_zemauth_permission_cache"
        if not hasattr(self, perm_cache_name):
            if self.is_superuser:
                perms = auth_models.Permission.objects.all().exclude(codename__in=SUPERUSER_EXCLUDED_PERMISSIONS)
            else:
                perms = (
                    auth_models.Permission.objects.filter(
                        models.Q(id__in=self.user_permissions.all()) | models.Q(group__in=self.groups.all())
                    )
                    .order_by("id")
                    .distinct("id")
                )

            perms = perms.select_related("content_type")

            public_permissions = auth_models.Permission.objects.filter(pk__in=(x.pk for x in perms)).filter(
                group__in=auth_models.Group.objects.filter(internalgroup=None)
            )

            public_permissions_ids = [x.pk for x in public_permissions]

            permissions = {
                "{}.{}".format(x.content_type.app_label, x.codename): x.pk in public_permissions_ids for x in perms
            }

            setattr(self, perm_cache_name, permissions)

        return getattr(self, perm_cache_name)

    def is_self_managed(self):
        return self.email and "@zemanta" not in self.email.lower()

    def get_sspd_sources(self):
        if self.has_perm("zemauth.sspd_can_see_all_sources"):
            sources = core.models.Source.objects.filter(deprecated=False)
        else:
            sources = self.sspd_sources.all()

        result = []
        for source in sources:
            result.append(str(source.id))

        return result

    def get_sspd_sources_markets(self):
        if self.has_perm("zemauth.sspd_can_see_all_sources"):
            return {"*": ["*"]}
        else:
            return self.sspd_sources_markets

    @transaction.atomic
    def update(self, **kwargs):
        updates = self._clean_updates(kwargs)
        if not updates:
            return

        self.validate(updates)
        self._apply_updates_and_save(**updates)

    def _clean_updates(self, updates):
        cleaned_updates = {}

        for field, value in updates.items():
            if field in set(self._settings_fields) and value != getattr(self, field):
                cleaned_updates[field] = value

        return cleaned_updates

    def _apply_updates_and_save(self, **updates):
        for field, value in updates.items():
            if field in self._settings_fields:
                setattr(self, field, value)
        self.save()
