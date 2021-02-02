import datetime
import hashlib
import hmac

import pytz
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.db import models
from django.db import transaction
from django.utils.functional import cached_property

import core.models
from zemauth.features.entity_permission import Permission


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
        permissions = self.all_permissions
        if len(permissions) == 0:
            return {}

        return {x["permission"]: x["is_public"] for x in permissions}

    @cached_property
    def all_permissions(self):
        if not self.is_active or self.is_anonymous:
            return []

        if self.is_superuser:
            permissions = list(auth_models.Permission.objects.all())
        else:
            permissions = list(
                auth_models.Permission.objects.filter(
                    models.Q(id__in=self.user_permissions.all()) | models.Q(group__in=self.groups.all())
                )
                .order_by("id")
                .distinct("id")
            )

        public_permissions_ids = (
            auth_models.Permission.objects.filter(pk__in=(x.pk for x in permissions))
            .filter(group__in=auth_models.Group.objects.filter(internalgroup=None))
            .values_list("id", flat=True)
        )

        return [
            {
                "permission": "{}.{}".format(x.content_type.app_label, x.codename),
                "is_public": x.pk in public_permissions_ids,
            }
            for x in permissions
        ]

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

    @staticmethod
    def get_timezone_offset():
        return (
            pytz.timezone(settings.DEFAULT_TIME_ZONE).utcoffset(datetime.datetime.utcnow(), is_dst=True).total_seconds()
        )

    def get_intercom_user_hash(self):
        return hmac.new(
            settings.INTERCOM_ID_VERIFICATION_SECRET, self.email.encode("utf-8"), digestmod=hashlib.sha256
        ).hexdigest()

    def get_default_csv_separator(self):
        agencies = [ep.agency for ep in self.all_entity_permissions if ep.agency and ep.permission == Permission.READ]
        return agencies[0].default_csv_separator if agencies else None

    def get_default_csv_decimal_separator(self):
        agencies = [ep.agency for ep in self.all_entity_permissions if ep.agency and ep.permission == Permission.READ]
        return agencies[0].default_csv_decimal_separator if agencies else None

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
