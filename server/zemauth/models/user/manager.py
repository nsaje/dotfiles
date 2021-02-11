# -*- coding: utf-8 -*-

import operator
from functools import reduce

from django.contrib.auth import models as auth_models
from django.db import models
from django.utils import timezone


class UserManager(auth_models.BaseUserManager):
    def create_user(self, email, password=None, is_active=True, **extra_fields):
        return self._create_user(email, password, is_active, False, False, **extra_fields)

    def create_superuser(self, email, password, is_active=True, **extra_fields):
        return self._create_user(email, password, is_active, True, True, **extra_fields)

    def get_or_create_service_user(self, service_name):
        user, _ = self.get_or_create(
            username=service_name, email="%s@service.zemanta.com" % service_name, is_service=True
        )
        return user

    def get_users_with_perm(self, perm_name, include_superusers=False):
        perm = auth_models.Permission.objects.get(codename=perm_name)

        query_list = [models.Q(groups__permissions=perm), models.Q(user_permissions=perm)]

        if include_superusers:
            query_list.append(models.Q(is_superuser=True))

        return self.filter(reduce(operator.or_, query_list)).distinct()

    def _create_user(self, email, password, is_active, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields,
        )
        user.set_password(password)
        user.save()
        return user
