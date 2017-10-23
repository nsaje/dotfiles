# -*- coding: utf-8 -*-

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

import core.common
import core.entity.helpers
import core.history
import core.source

import bcm_mixin

# These agencies should have campaign stop turned off
# (for example Outbrain)
AGENCIES_WITHOUT_CAMPAIGN_STOP = {55}
ACCOUNTS_WITHOUT_CAMPAIGN_STOP = {490}


class CampaignManager(core.common.QuerySetManager):

    @transaction.atomic
    def create(self, request, account, name, iab_category=constants.IABCategory.IAB24):
        campaign = Campaign(
            name=name,
            account=account
        )
        campaign.save(request=request)

        settings = campaign.get_current_settings()  # creates new settings with default values
        settings.name = name
        settings.campaign_manager = request.user if request else None
        settings.iab_category = iab_category

        if account.id in ACCOUNTS_WITHOUT_CAMPAIGN_STOP or account.agency_id in AGENCIES_WITHOUT_CAMPAIGN_STOP:
            settings.automatic_campaign_stop = False

        settings.save(request=request, action_type=constants.HistoryActionType.CREATE)

        return campaign


class Campaign(models.Model, core.common.PermissionMixin, bcm_mixin.CampaignBCMMixin):
    class Meta:
        app_label = 'dash'

    _demo_fields = {'name': utils.demo_anonymizer.campaign_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    account = models.ForeignKey('Account', on_delete=models.PROTECT)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    groups = models.ManyToManyField(auth_models.Group)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT, null=True)

    default_whitelist = models.ForeignKey('PublisherGroup', related_name='whitelisted_campaigns',
                                          on_delete=models.PROTECT, null=True, blank=True)
    default_blacklist = models.ForeignKey('PublisherGroup', related_name='blacklisted_campaigns',
                                          on_delete=models.PROTECT, null=True, blank=True)
    custom_flags = JSONField(null=True, blank=True)

    USERS_FIELD = 'users'

    objects = CampaignManager()

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    def get_campaign_url(self, request):
        campaign_settings_url = request.build_absolute_uri(
            reverse('admin:dash_campaign_change', args=(self.pk,))
        )
        campaign_settings_url = campaign_settings_url.replace(
            'http://', 'https://')
        return campaign_settings_url

    def get_long_name(self):
        return u'{}, Campaign {}'.format(self.account.get_long_name(), self.name)

    admin_link.allow_tags = True

    def get_sales_representative(self):
        return self.account.get_current_settings().default_sales_representative

    def get_cs_representative(self):
        return self.account.get_current_settings().default_cs_representative

    def get_current_settings(self):
        # FIXME:circular dependency
        import core.entity.settings
        if not self.pk:
            raise exc.BaseError(
                'Campaign settings can\'t be fetched because campaign hasn\'t been saved yet.'
            )

        settings = core.entity.settings.CampaignSettings.objects.\
            filter(campaign_id=self.pk).\
            order_by('-created_dt').first()
        if not settings:
            settings = core.entity.settings.CampaignSettings(
                campaign=self, **core.entity.settings.CampaignSettings.get_defaults_dict())

        return settings

    def can_archive(self):
        for ad_group in self.adgroup_set.all():
            if not ad_group.can_archive():
                return False

        for budget in self.budgets.all():
            if budget.state() in (constants.BudgetLineItemState.ACTIVE,
                                  constants.BudgetLineItemState.PENDING):
                return False

        return True

    def can_restore(self):
        if self.account.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Campaign can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for ad_group in self.adgroup_set.all():
                ad_group.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(
                request,
                action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Campaign can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(
                request,
                action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    def is_in_landing(self):
        current_settings = self.get_current_settings()
        return current_settings.landing_mode

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, account, agency = core.entity.helpers._generate_parents(campaign=self)
        return core.history.History.objects.create(
            campaign=self,
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.CAMPAIGN,
            action_type=action_type
        )

    def get_default_blacklist_name(self):
        return u"Default blacklist for campaign {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return u"Default whitelist for campaign {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.CAMPAIGN

    def get_account(self):
        return self.account

    def save(self, request=None, user=None, *args, **kwargs):
        self.modified_by = None
        if request is not None:
            self.modified_by = request.user
        if user is not None:
            self.modified_by = user
        super(Campaign, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id) |
                models.Q(account__users__id=user.id) |
                models.Q(account__groups__user__id=user.id) |
                models.Q(account__agency__users__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(adgroup__adgroupsource__source__in=sources).distinct()

        def filter_by_agencies(self, agencies):
            if not agencies:
                return self
            return self.filter(
                account__agency__in=agencies)

        def filter_by_account_types(self, account_types):
            # FIXME:circular dependency
            import core.entity.settings
            if not account_types:
                return self

            latest_settings = core.entity.settings.AccountSettings.objects.all().filter(
                account__campaign__in=self
            ).group_current_settings()

            filtered_accounts = core.entity.settings.AccountSettings.objects.all().filter(
                id__in=latest_settings
            ).filter(
                account_type__in=account_types
            ).values_list('account__id', flat=True)

            return self.filter(
                account__id__in=filtered_accounts
            )

        def exclude_archived(self, show_archived=False):
            # FIXME:circular dependency
            import core.entity.settings
            if show_archived:
                return self

            related_settings = core.entity.settings.CampaignSettings.objects.all().filter(
                campaign__in=self
            ).group_current_settings()

            archived_campaigns = core.entity.settings.CampaignSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list(
                'campaign__id', flat=True
            )
            return self.exclude(pk__in=archived_campaigns)

        def exclude_landing(self):
            # FIXME:circular dependency
            import core.entity.settings
            related_settings = core.entity.settings.CampaignSettings.objects.all().filter(
                campaign__in=self
            ).group_current_settings()

            excluded = core.entity.settings.CampaignSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                models.Q(automatic_campaign_stop=False) |
                models.Q(landing_mode=True)
            ).values_list(
                'campaign__id', flat=True
            )

            return self.exclude(pk__in=excluded)

        def filter_landing(self):
            # FIXME:circular dependency
            import core.entity.settings
            related_settings = core.entity.settings.CampaignSettings.objects.all().filter(
                campaign__in=self
            ).group_current_settings()

            filtered = core.entity.settings.CampaignSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                automatic_campaign_stop=True,
                landing_mode=True
            ).values_list(
                'campaign__id', flat=True
            )

            return self.filter(pk__in=filtered)
