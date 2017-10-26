# -*- coding: utf-8 -*-
import newrelic.agent
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.postgres.fields import JSONField
from django.core.urlresolvers import reverse
from django.db import models, transaction

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils import exc
from utils import json_helper

import core.bcm
import core.common
import core.history
import core.entity
import core.entity.helpers

import manager


class Account(models.Model, core.common.SettingsProxyMixin):

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ('group_account_automatically_add',
             'All new accounts are automatically added to group.'),
        )
        app_label = 'dash'

    _demo_fields = {'name': utils.demo_anonymizer.account_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=False,
        blank=False,
        null=False
    )
    agency = models.ForeignKey(
        'Agency', on_delete=models.PROTECT, null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    groups = models.ManyToManyField(auth_models.Group)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    related_name='+', on_delete=models.PROTECT)

    default_whitelist = models.ForeignKey('PublisherGroup', related_name='whitelisted_accounts',
                                          on_delete=models.PROTECT, null=True, blank=True)
    default_blacklist = models.ForeignKey('PublisherGroup', related_name='blacklisted_accounts',
                                          on_delete=models.PROTECT, null=True, blank=True)

    allowed_sources = models.ManyToManyField('Source')

    outbrain_marketer_id = models.CharField(
        null=True, blank=True, max_length=255)

    salesforce_url = models.URLField(null=True, blank=True, max_length=255)

    # migration to the new system introduced by margings and fees project
    uses_bcm_v2 = models.BooleanField(
        default=False,
        verbose_name='Margins v2',
        help_text='This account will have license fee and margin included into all costs.'
    )
    custom_flags = JSONField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_long_name(self):
        agency = ''
        if self.agency:
            agency = self.agency.get_long_name() + u', '
        return u'{}Account {}'.format(agency, self.name)

    def get_salesforce_id(self):
        return 'b{}'.format(self.pk)

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Account settings can\'t be fetched because acount hasn\'t been saved yet.'
            )

        # FIXME:circular dependency
        import core.entity.settings
        settings = core.entity.settings.AccountSettings.objects.\
            filter(account_id=self.pk).\
            order_by('-created_dt').first()
        if not settings:
            settings = core.entity.settings.AccountSettings(
                account=self,
                name=self.name,
            )

        return settings

    @newrelic.agent.function_trace()
    def can_archive(self):
        for campaign in self.campaign_set.all():
            if not campaign.can_archive():
                return False

        return True

    @newrelic.agent.function_trace()
    def can_restore(self):
        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    def is_agency(self):
        return self.agency is not None

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Account can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for campaign in self.campaign_set.all():
                campaign.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(
                request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(
                request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/account/%d/">Edit</a>' % self.id
        else:
            return 'N/A'
    admin_link.allow_tags = True

    def get_account_url(self, request):
        account_settings_url = request.build_absolute_uri(
            reverse('admin:dash_account_change', args=(self.pk,))
        )
        campaign_settings_url = account_settings_url.replace(
            'http://', 'https://')
        return campaign_settings_url

    def get_default_blacklist_name(self):
        return u"Default blacklist for account {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return u"Default whitelist for account {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.ACCOUNT

    def get_account(self):
        return self

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, _, agency = core.entity.helpers.generate_parents(account=self)
        return core.history.History.objects.create(
            account=self,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.ACCOUNT,
            action_type=action_type
        )

    def set_uses_bcm_v2(self, request, enabled):
        self.uses_bcm_v2 = bool(enabled)
        self.save(request)

    @transaction.atomic
    def migrate_to_bcm_v2(self, request):
        if self.uses_bcm_v2:
            return

        for campaign in self.campaign_set.all():
            campaign.migrate_to_bcm_v2(request)

        self.set_uses_bcm_v2(request, True)
        self._migrate_agency(request)

    def _migrate_agency(self, request):
        if self.agency and self.agency.account_set.all_use_bcm_v2():
            self.agency.set_new_accounts_use_bcm_v2(request, True)

    def get_all_custom_flags(self):
        custom_flags = self.agency.custom_flags if self.agency else {}
        custom_flags.update(self.custom_flags or {})
        return custom_flags

    def save(self, request, *args, **kwargs):
        if request and not request.user.is_anonymous():
            self.modified_by = request.user
        super(Account, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id) |
                models.Q(agency__users__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self
            return self.filter(
                campaign__adgroup__adgroupsource__source__id__in=sources).distinct()

        def filter_by_agencies(self, agencies):
            if not agencies:
                return self
            return self.filter(
                agency__in=agencies)

        def filter_by_account_types(self, account_types):
            # FIXME:circular dependency
            import core.entity.settings
            if not account_types:
                return self
            latest_settings = core.entity.settings.AccountSettings.objects.all().filter(
                account__in=self
            ).group_current_settings()

            filtered_ac_ids = core.entity.settings.AccountSettings.objects.all().filter(
                id__in=latest_settings,
                account_type__in=account_types
            ).values_list('account__id', flat=True)

            return self.filter(id__in=filtered_ac_ids)

        def exclude_archived(self, show_archived=False):
            # FIXME:circular dependency
            import core.entity.settings
            if show_archived:
                return self

            related_settings = core.entity.settings.AccountSettings.objects.all().filter(
                account__in=self
            ).group_current_settings()

            archived_accounts = core.entity.settings.AccountSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list(
                'account__id', flat=True
            )
            return self.exclude(pk__in=archived_accounts)

        def filter_with_spend(self):
            return self.filter(
                pk__in=set(core.bcm.BudgetDailyStatement.objects.filter(
                    budget__campaign__account_id__in=self
                ).filter(
                    media_spend_nano__gt=0
                ).values_list(
                    'budget__campaign__account_id', flat=True
                ))
            )

        def all_use_bcm_v2(self):
            return all(self.values_list('uses_bcm_v2', flat=True))

    objects = manager.AccountManager.from_queryset(QuerySet)()
