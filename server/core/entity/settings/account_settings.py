# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db import transaction

import utils.demo_anonymizer
import utils.string_helper
from dash import constants

import core.common
import core.history
import core.source

from settings_base import SettingsBase
from settings_query_set import SettingsQuerySet


class AccountSettings(SettingsBase):
    class Meta:
        app_label = 'dash'
        ordering = ('-created_dt',)

    _demo_fields = {
        'name': utils.demo_anonymizer.account_name_from_pool
    }
    _settings_fields = [
        'name',
        'archived',
        'default_account_manager',
        'default_sales_representative',
        'default_cs_representative',
        'account_type',
        'whitelist_publisher_groups',
        'blacklist_publisher_groups',
        'salesforce_url',
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    account = models.ForeignKey('Account', on_delete=models.PROTECT)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    default_account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    default_sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    default_cs_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    account_type = models.IntegerField(
        default=constants.AccountType.UNKNOWN,
        choices=constants.AccountType.get_choices()
    )

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    salesforce_url = models.URLField(null=True, blank=True, max_length=255)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    objects = core.common.QuerySetManager()

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'name': 'Name',
            'archived': 'Archived',
            'default_account_manager': 'Account Manager',
            'default_sales_representative': 'Sales Representative',
            'default_cs_representative': 'Customer Success Representative',
            'account_type': 'Account Type',
            'whitelist_publisher_groups': 'Whitelist publisher groups',
            'blacklist_publisher_groups': 'Blacklist publisher groups',
            'salesforce_url': 'SalesForce',
        }
        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'archived':
            value = str(value)
        elif prop_name in ('default_account_manager',
                           'default_sales_representative',
                           'default_cs_representative'):
            # FIXME:circular dependency
            import dash.views.helpers
            value = dash.views.helpers.get_user_full_name_or_email(
                value).decode('utf-8')
        elif prop_name in ('whitelist_publisher_groups', 'blacklist_publisher_groups'):
            if not value:
                value = ''
            else:
                names = core.publisher_groups.PublisherGroup.objects.filter(pk__in=value).values_list('name', flat=True)
                value = ', '.join(names)
        elif prop_name == 'account_type':
            value = constants.AccountType.get_text(value)
        return value

    @transaction.atomic
    def update(self, request, **kwargs):
        new_settings = self.copy_settings()
        valid_fields = set(self._settings_fields)

        for field, value in kwargs.items():
            if field in valid_fields:
                setattr(new_settings, field, value)
        new_settings.save(request)
        return new_settings

    def save(self,
             request,
             action_type=None,
             changes_text=None,
             *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user
        super(AccountSettings, self).save(*args, **kwargs)
        self.add_to_history(request and request.user,
                            action_type, changes_text)

    def add_to_history(self, user, action_type, history_changes_text):
        changes = self.get_model_state_changes(
            self.get_settings_dict()
        )
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return
        if 'salesforce_url' in changes:
            return

        changes_text = history_changes_text or self.get_changes_text_from_dict(
            changes)
        self.account.write_history(
            changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
        )

    class QuerySet(SettingsQuerySet):

        def group_current_settings(self):
            return self.order_by('account_id', '-created_dt').distinct('account')
