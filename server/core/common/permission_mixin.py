# -*- coding: utf-8 -*-

from django.contrib import auth


class PermissionMixin(object):
    USERS_FIELD = ""

    def has_permission(self, user, permission=None):
        try:
            if user.is_superuser or (
                (not permission or user.has_perm(permission))
                and getattr(self, self.USERS_FIELD).filter(id=user.id).exists()
            ):
                return True
        except auth.get_user_model().DoesNotExist:
            return False

        return False
