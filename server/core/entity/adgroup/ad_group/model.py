# -*- coding: utf-8 -*-
import datetime

import newrelic.agent
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.template.defaultfilters import pluralize

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils import dates_helper
from utils import exc
from utils import json_helper
from utils import k1_helper
from utils import redirector_helper

import core.bcm
import core.common
import core.history
import core.source
import core.entity

import bcm_mixin


class AdGroupManager(core.common.QuerySetManager):

    def _create_default_name(self, campaign):
        return core.entity.helpers.create_default_name(
            AdGroup.objects.filter(campaign=campaign), 'New ad group')

    def _create(self, request, campaign, name, **kwargs):
        ad_group = AdGroup(campaign=campaign, name=name, **kwargs)
        ad_group.save(request)
        return ad_group

    def _post_create(self, ad_group, ad_group_settings):
        if ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            from automation import autopilot_plus
            autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group_settings, send_mail=False)

        k1_helper.update_ad_group(ad_group.pk, msg='CampaignAdGroups.put')
        redirector_helper.insert_adgroup(ad_group, ad_group_settings, ad_group.campaign.get_current_settings())

    def create(self, request, campaign, is_restapi=False, name=None, **kwargs):
        core.common.entity_limits.enforce(
            AdGroup.objects.filter(campaign=campaign).exclude_archived(),
            campaign.account_id,
        )
        with transaction.atomic():
            if name is None:
                name = self._create_default_name(campaign)
            ad_group = self._create(request, campaign, name=name)

            if is_restapi:
                ad_group_settings = core.entity.settings.AdGroupSettings.objects.create_restapi_default(
                    ad_group, name=name)
            else:
                ad_group_settings = core.entity.settings.AdGroupSettings.objects.create_default(ad_group, name=name)

            core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
                request, ad_group, write_history=False, k1_sync=False)

        self._post_create(ad_group, ad_group_settings)
        ad_group.write_history_created(request)
        return ad_group

    def clone(self, request, source_ad_group, campaign, new_name):
        core.common.entity_limits.enforce(
            AdGroup.objects.filter(campaign=campaign).exclude_archived(),
            campaign.account_id,
        )
        if campaign.get_current_settings().landing_mode:
            raise exc.ValidationError('Please select a destination campaign that is not in landing mode')

        with transaction.atomic():
            ad_group = self._create(request, campaign, name=new_name)
            ad_group_settings = core.entity.settings.AdGroupSettings.objects.clone(
                request, ad_group, source_ad_group.get_current_settings())

            core.entity.AdGroupSource.objects.bulk_clone_on_allowed_sources(
                request, ad_group, source_ad_group, write_history=False, k1_sync=False)

        self._post_create(ad_group, ad_group_settings)
        ad_group.write_history_cloned_from(request, source_ad_group)
        source_ad_group.write_history_cloned_to(request, ad_group)
        return ad_group


class AdGroup(models.Model, core.common.SettingsProxyMixin, bcm_mixin.AdGroupBCMMixin):
    _current_settings = None

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

    custom_flags = JSONField(null=True, blank=True)

    objects = AdGroupManager()

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

    def write_history_created(self, request):
        source_names = list(self.adgroupsource_set.all().values_list('source__name', flat=True))
        if source_names:
            changes_text = 'Created settings and automatically created campaigns for {} sources ({})'.format(
                len(source_names), ', '.join(source_names))
        else:
            changes_text = None

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_cloned_to(self, request, destination_ad_group):
        changes_text = u'This Ad group was cloned to {}'.format(destination_ad_group.get_name_with_id())
        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_cloned_from(self, request, source_ad_group):
        source_names = list(self.adgroupsource_set.all().values_list('source__name', flat=True))
        if source_names:
            changes_text = u'Cloned settings and content ads from {} and automatically created campaigns for {} sources ({})'.format(
                source_ad_group.get_name_with_id(),
                len(source_names), ', '.join(source_names))
        else:
            changes_text = None

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_content_ads_cloned(self, request, content_ads, batch, source_ad_group, overriden_state):
        state_text = u'Cloned content ads state was left intact.'
        if overriden_state is not None:
            state_text = u'State of all cloned content ads was set to "{}".'.format(
                constants.ContentAdSourceState.get_text(overriden_state))

        changes_text = u'Cloned {} content ad{} from "{}" as batch "{}". {}'.format(
            len(content_ads),
            pluralize(len(content_ads)),
            source_ad_group.get_name_with_id(),
            batch.name,
            state_text)

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_source_added(self, request, ad_group_source):
        self.write_history(
            '{} campaign created.'.format(ad_group_source.source.name),
            user=request.user,
            action_type=constants.HistoryActionType.MEDIA_SOURCE_ADD)

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None,
                      action_type=None):
        if not changes and not changes_text:
            return  # nothing to write

        campaign, account, agency = core.entity.helpers.generate_parents(ad_group=self)
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

    def get_all_custom_flags(self):
        custom_flags = self.campaign.get_all_custom_flags()
        custom_flags.update(self.custom_flags or {})
        return custom_flags

    def get_name_with_id(self):
        return u"{} ({})".format(self.name, self.id)

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user
        super(AdGroup, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            if user.has_perm('zemauth.can_see_all_accounts'):
                return self
            return self.filter(
                models.Q(campaign__account__users__id=user.id) |
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

            return self.filter(adgroupsource__source__in=sources).distinct()

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
