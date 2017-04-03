# -*- coding: utf-8 -*-
import datetime

import newrelic.agent
from django.conf import settings
from django.db import models, transaction

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils import dates_helper
from utils import exc
from utils import json_helper

import core.common
import core.history
import core.source
import core.entity.helpers


class AdGroup(models.Model):
    class Meta:
        app_label = 'dash'
        ordering = ('name',)

    _demo_fields = {'name': utils.demo_anonymizer.ad_group_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey('Campaign', on_delete=models.PROTECT)
    sources = models.ManyToManyField(core.source.Source, through='AdGroupSource')
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    default_whitelist = models.ForeignKey('PublisherGroup', related_name='whitelisted_ad_groups',
                                          on_delete=models.PROTECT, null=True, blank=True)
    default_blacklist = models.ForeignKey('PublisherGroup', related_name='blacklisted_ad_groups',
                                          on_delete=models.PROTECT, null=True, blank=True)

    objects = core.common.QuerySetManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/'

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/adgroup/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True

    @newrelic.agent.function_trace()
    def get_current_settings(self):
        # FIXME:circular dependency
        import core.entity.settings
        if not self.pk:
            raise exc.BaseError(
                'Ad group setting couldn\'t be fetched because ad group hasn\'t been saved yet.'
            )

        settings = core.entity.settings.AdGroupSettings.objects.\
            filter(ad_group_id=self.pk).\
            order_by('created_dt').last()
        if settings is None:
            settings = core.entity.settings.AdGroupSettings(
                ad_group=self, **core.entity.settings.AdGroupSettings.get_defaults_dict())

        return settings

    def can_archive(self):
        # FIXME:circular dependency
        import core.entity.settings
        current_settings = self.get_current_settings()

        # can not archive when ad group is active
        if self.is_ad_group_active(current_settings):
            return False

        if not core.entity.settings.AdGroupSettings.objects.filter(
                ad_group_id=self.id,
                state=constants.AdGroupSettingsState.ACTIVE
        ).exists():
            # if it was never turned on than it can be archived
            return True

        # can not archive if ad group was turned off in the last 3 days
        today = dates_helper.local_today()
        activated_settings = core.entity.settings.AdGroupSettings.objects.filter(
            ad_group_id=self.id,
            created_dt__gte=today - datetime.timedelta(days=core.entity.helpers.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL),
            state=constants.AdGroupSettingsState.INACTIVE
        )
        return not activated_settings.exists()

    def can_restore(self):
        if self.campaign.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @classmethod
    def get_running_status(cls, ad_group_settings):
        """
        Returns the actual running status of ad group settings with selected sources settings.
        """

        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        if cls.get_running_status_by_flight_time(ad_group_settings) == constants.AdGroupRunningStatus.ACTIVE:
            return constants.AdGroupRunningStatus.ACTIVE

        return constants.AdGroupRunningStatus.INACTIVE

    def get_sources_state(self):
        # FIXME:circular dependency
        import core.entity.settings
        settings = self.get_current_settings()

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=self,
        ).group_current_settings().values('ad_group_source__source_id', 'state')

        states = {}
        for source_settings in ad_group_source_settings:
            state = source_settings['state']
            if state == constants.AdGroupSourceSettingsState.ACTIVE:
                state = settings.state

            states[source_settings['ad_group_source__source_id']] = state

        return states

    @classmethod
    def get_running_status_by_flight_time(cls, ad_group_settings):
        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        now = dates_helper.local_today()
        if ad_group_settings.start_date <= now and\
           (ad_group_settings.end_date is None or now <= ad_group_settings.end_date):
            return constants.AdGroupRunningStatus.ACTIVE
        return constants.AdGroupRunningStatus.INACTIVE

    @classmethod
    def get_running_status_by_sources_setting(cls, ad_group_settings, ad_group_sources_settings):
        """
        Returns "running" when at least one of the ad group sources settings status is
        set to be active.
        """

        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        if ad_group_sources_settings and\
           any(x.state == constants.AdGroupSourceSettingsState.ACTIVE for x in ad_group_sources_settings):
            return constants.AdGroupRunningStatus.ACTIVE
        return constants.AdGroupRunningStatus.INACTIVE

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.campaign.account.name
        campaign_name = self.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.name
        else:
            ad_group_name = new_adgroup_name
        return u'ONE: {} / {} / {} / {}'.format(
            core.entity.helpers.shorten_name(account_name),
            core.entity.helpers.shorten_name(campaign_name),
            core.entity.helpers.shorten_name(ad_group_name),
            self.id
        )

    @classmethod
    def is_ad_group_active(cls, ad_group_settings):
        if ad_group_settings and ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
            return True
        return False

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'An ad group has to be paused for 3 days in order to archive it.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(
                request,
                action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account and campaign have to not be archived in order to restore an ad group.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(
                request,
                action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def set_state(self, request, new_state):
        current_settings = self.get_current_settings()

        if current_settings.state != new_state:
            new_settings = current_settings.copy_settings()
            new_settings.state = new_state
            new_settings.save(
                request, action_type=constants.HistoryActionType.SETTINGS_CHANGE)
            return True

        return False

    def get_default_blacklist_name(self):
        return u"Default blacklist for ad group {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return u"Default whitelist for ad group {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.ADGROUP

    def get_account(self):
        return self.campaign.account

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None,
                      action_type=None):
        if not changes and not changes_text:
            return  # nothing to write

        campaign, account, agency = core.entity.helpers._generate_parents(ad_group=self)
        history = core.history.History.objects.create(
            ad_group=self,
            campaign=campaign,
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.AD_GROUP,
            action_type=action_type
        )
        return history

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user
        super(AdGroup, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(campaign__users__id=user.id) |
                models.Q(campaign__groups__user__id=user.id) |
                models.Q(campaign__account__users__id=user.id) |
                models.Q(campaign__account__groups__user__id=user.id) |
                models.Q(campaign__account__agency__users__id=user.id)
            ).distinct()

        def filter_by_agencies(self, agencies):
            if not agencies:
                return self
            return self.filter(
                campaign__account__agency__in=agencies)

        def filter_by_account_types(self, account_types):
            # FIXME:circular dependency
            import core.entity.settings
            if not account_types:
                return self

            latest_settings = core.entity.settings.AccountSettings.objects.all().filter(
                account__campaign__adgroup__in=self
            ).group_current_settings()

            filtered_accounts = core.entity.settings.AccountSettings.objects.all().filter(
                id__in=latest_settings,
                account_type__in=account_types
            ).values_list('account__id', flat=True)

            return self.filter(
                campaign__account__in=filtered_accounts)

        def filter_by_sources(self, sources):
            # FIXME:circular dependency
            import core.entity.settings
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(adgroupsource__source__in=sources)

        def exclude_archived(self, show_archived=False):
            # FIXME:circular dependency
            import core.entity.settings
            if show_archived:
                return self

            related_settings = core.entity.settings.AdGroupSettings.objects.all().filter(
                ad_group__in=self
            ).group_current_settings()

            archived_adgroups = core.entity.settings.AdGroupSettings.objects.filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list('ad_group', flat=True)

            return self.exclude(pk__in=archived_adgroups)

        def filter_running(self, date=None):
            # FIXME:circular dependency
            import core.entity.settings
            """
            This function checks if adgroup is running on arbitrary number of adgroups
            with a fixed amount of queries.
            An adgroup is running if:
                - it was set as active(adgroupsettings)
                - current date is between start and stop(flight time)
            """
            if not date:
                date = dates_helper.local_today()
            latest_ad_group_settings = core.entity.settings.AdGroupSettings.objects.filter(
                ad_group__in=self
            ).group_current_settings()

            ad_group_settings = core.entity.settings.AdGroupSettings.objects.filter(
                pk__in=latest_ad_group_settings
            ).filter(
                state=constants.AdGroupSettingsState.ACTIVE,
                start_date__lte=date
            ).exclude(
                end_date__isnull=False,
                end_date__lt=date
            ).values_list('ad_group__id', flat=True)

            ids = set(ad_group_settings)
            return self.filter(id__in=ids)

        def filter_active(self):
            # FIXME:circular dependency
            import core.entity.settings
            """
            Returns only ad groups that have settings set to active.
            """
            latest_ad_group_settings = core.entity.settings.AdGroupSettings.objects.\
                filter(ad_group__in=self).\
                group_current_settings()
            active_ad_group_ids = core.entity.settings.AdGroupSettings.objects.\
                filter(id__in=latest_ad_group_settings).\
                filter(state=constants.AdGroupSettingsState.ACTIVE).\
                values_list('ad_group_id', flat=True)
            return self.filter(id__in=active_ad_group_ids)

        def filter_landing(self):
            # FIXME:circular dependency
            import core.entity.settings
            related_settings = core.entity.settings.AdGroupSettings.objects.all().filter(
                ad_group__in=self
            ).group_current_settings()

            filtered = core.entity.settings.AdGroupSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                landing_mode=True
            ).values_list(
                'ad_group__id', flat=True
            )

            return self.filter(pk__in=filtered)
