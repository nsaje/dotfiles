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
from utils import json_helper
from utils import k1_helper
from utils import redirector_helper
from dash.features import custom_flags

import core.bcm
import core.common
import core.history
import core.entity
import core.source

from . import bcm_mixin


AMPLIFY_REVIEW_AGENCIES_DISABLED = {55}  # Outbrain
AMPLIFY_REVIEW_ACCOUNTS_DISABLED = {490}  # inPowered


class AdGroupManager(core.common.QuerySetManager):
    def _create_default_name(self, campaign):
        return core.entity.helpers.create_default_name(AdGroup.objects.filter(campaign=campaign), "New ad group")

    def _create(self, request, campaign, name, **kwargs):
        ad_group = AdGroup(campaign=campaign, name=name, **kwargs)
        if (
            settings.AMPLIFY_REVIEW
            and campaign.account_id not in AMPLIFY_REVIEW_ACCOUNTS_DISABLED
            and campaign.account.agency_id not in AMPLIFY_REVIEW_AGENCIES_DISABLED
        ):
            ad_group.amplify_review = True
        ad_group.save(request)
        return ad_group

    def _post_create(self, ad_group):
        if (
            ad_group.settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            or ad_group.campaign.settings.autopilot
        ):
            from automation import autopilot

            autopilot.recalculate_budgets_ad_group(ad_group, send_mail=False)

        k1_helper.update_ad_group(ad_group.pk, msg="CampaignAdGroups.put")
        redirector_helper.insert_adgroup(ad_group)

    def create(self, request, campaign, is_restapi=False, name=None, **kwargs):
        core.common.entity_limits.enforce(
            AdGroup.objects.filter(campaign=campaign).exclude_archived(), campaign.account_id
        )
        with transaction.atomic():
            if name is None:
                name = self._create_default_name(campaign)
            ad_group = self._create(request, campaign, name=name)

            if is_restapi:
                ad_group.settings = core.entity.settings.AdGroupSettings.objects.create_restapi_default(
                    ad_group, name=name
                )
            else:
                ad_group.settings = core.entity.settings.AdGroupSettings.objects.create_default(ad_group, name=name)
            ad_group.save(request)

            core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
                request, ad_group, write_history=False, k1_sync=False
            )
            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

        self._post_create(ad_group)
        ad_group.write_history_created(request)
        return ad_group

    def clone(self, request, source_ad_group, campaign, new_name):
        core.common.entity_limits.enforce(
            AdGroup.objects.filter(campaign=campaign).exclude_archived(), campaign.account_id
        )

        with transaction.atomic():
            ad_group = self._create(request, campaign, name=new_name)
            ad_group.settings = core.entity.settings.AdGroupSettings.objects.clone(
                request, ad_group, source_ad_group.get_current_settings()
            )
            ad_group.save(request)

            core.entity.AdGroupSource.objects.bulk_clone_on_allowed_sources(
                request, ad_group, source_ad_group, write_history=False, k1_sync=False
            )
            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

        self._post_create(ad_group)
        ad_group.write_history_cloned_from(request, source_ad_group)
        source_ad_group.write_history_cloned_to(request, ad_group)
        return ad_group


class AdGroup(models.Model, bcm_mixin.AdGroupBCMMixin):
    _current_settings = None

    class Meta:
        app_label = "dash"
        ordering = ("name",)

    _demo_fields = {"name": utils.demo_anonymizer.ad_group_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    campaign = models.ForeignKey("Campaign", on_delete=models.PROTECT)
    sources = models.ManyToManyField("Source", through="AdGroupSource")
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT)

    default_whitelist = models.ForeignKey(
        "PublisherGroup", related_name="whitelisted_ad_groups", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.ForeignKey(
        "PublisherGroup", related_name="blacklisted_ad_groups", on_delete=models.PROTECT, null=True, blank=True
    )

    custom_flags = JSONField(null=True, blank=True)

    settings = models.OneToOneField(
        "AdGroupSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )
    amplify_review = models.NullBooleanField(default=None)

    objects = AdGroupManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/"

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/adgroup/%d/">Edit</a>' % self.id
        else:
            return "N/A"

    admin_link.allow_tags = True

    @newrelic.agent.function_trace()
    def get_current_settings(self):
        return self.settings

    def can_archive(self):
        # FIXME:circular dependency
        import core.entity.settings

        current_settings = self.get_current_settings()

        # can not archive when ad group is active
        if self.is_ad_group_active(current_settings):
            return False

        if not core.entity.settings.AdGroupSettings.objects.filter(
            ad_group_id=self.id, state=constants.AdGroupSettingsState.ACTIVE
        ).exists():
            # if it was never turned on than it can be archived
            return True

        # can not archive if ad group was turned off in the last 3 days
        today = dates_helper.local_today()
        activated_settings = core.entity.settings.AdGroupSettings.objects.filter(
            ad_group_id=self.id,
            created_dt__gte=today - datetime.timedelta(days=core.entity.helpers.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL),
            state=constants.AdGroupSettingsState.INACTIVE,
        )
        return not activated_settings.exists()

    def can_restore(self):
        if self.campaign.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    def is_blocked_by_custom_flag(self):
        return bool(self.get_all_custom_flags().get(custom_flags.constants.CUSTOMER_BLOCKED))

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

        ad_group_source_settings = (
            core.entity.settings.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=self)
            .group_current_settings()
            .values("ad_group_source__source_id", "state")
        )

        states = {}
        for source_settings in ad_group_source_settings:
            state = source_settings["state"]
            if state == constants.AdGroupSourceSettingsState.ACTIVE:
                state = settings.state

            states[source_settings["ad_group_source__source_id"]] = state

        return states

    @classmethod
    def get_running_status_by_flight_time(cls, ad_group_settings):
        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        now = dates_helper.local_today()
        if ad_group_settings.start_date <= now and (
            ad_group_settings.end_date is None or now <= ad_group_settings.end_date
        ):
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

        if ad_group_sources_settings and any(
            x.state == constants.AdGroupSourceSettingsState.ACTIVE for x in ad_group_sources_settings
        ):
            return constants.AdGroupRunningStatus.ACTIVE
        return constants.AdGroupRunningStatus.INACTIVE

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.campaign.account.name
        campaign_name = self.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.name
        else:
            ad_group_name = new_adgroup_name
        return "ONE: {} / {} / {} / {}".format(
            core.entity.helpers.shorten_name(account_name),
            core.entity.helpers.shorten_name(campaign_name),
            core.entity.helpers.shorten_name(ad_group_name),
            self.id,
        )

    @classmethod
    def is_ad_group_active(cls, ad_group_settings):
        if ad_group_settings and ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
            return True
        return False

    @transaction.atomic
    def archive(self, request):
        self.settings.update(request, archived=True)

    @transaction.atomic
    def restore(self, request):
        self.settings.update(request, archived=False)

    def get_default_blacklist_name(self):
        return "Default blacklist for ad group {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return "Default whitelist for ad group {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.ADGROUP

    def get_account(self):
        return self.campaign.account

    def write_history_created(self, request):
        source_names = list(self.adgroupsource_set.all().values_list("source__name", flat=True))
        if source_names:
            changes_text = "Created settings and automatically created campaigns for {} sources ({})".format(
                len(source_names), ", ".join(source_names)
            )
        else:
            changes_text = None

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_cloned_to(self, request, destination_ad_group):
        changes_text = "This Ad group was cloned to {}".format(destination_ad_group.get_name_with_id())
        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_cloned_from(self, request, source_ad_group):
        source_names = list(self.adgroupsource_set.all().values_list("source__name", flat=True))
        if source_names:
            changes_text = "Cloned settings and content ads from {} and automatically created campaigns for {} sources ({})".format(
                source_ad_group.get_name_with_id(), len(source_names), ", ".join(source_names)
            )
        else:
            changes_text = None

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_content_ads_cloned(self, request, content_ads, batch, source_ad_group, overriden_state):
        state_text = "Cloned content ads state was left intact."
        if overriden_state is not None:
            state_text = 'State of all cloned content ads was set to "{}".'.format(
                constants.ContentAdSourceState.get_text(overriden_state)
            )

        changes_text = 'Cloned {} content ad{} from "{}" as batch "{}". {}'.format(
            len(content_ads), pluralize(len(content_ads)), source_ad_group.get_name_with_id(), batch.name, state_text
        )

        self.write_history(changes_text, user=request.user, action_type=constants.HistoryActionType.CREATE)

    def write_history_source_added(self, request, ad_group_source):
        self.write_history(
            "{} campaign created.".format(ad_group_source.source.name),
            user=request.user,
            action_type=constants.HistoryActionType.MEDIA_SOURCE_ADD,
        )

    def write_history(self, changes_text, changes=None, user=None, system_user=None, action_type=None):
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
            action_type=action_type,
        )
        return history

    def get_all_custom_flags(self):
        custom_flags = self.campaign.get_all_custom_flags()
        if self.custom_flags:
            custom_flags.update({k: v for k, v in self.custom_flags.items() if v})
        return custom_flags

    def get_name_with_id(self):
        return "{} ({})".format(self.name, self.id)

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user if request else None
        super(AdGroup, self).save(*args, **kwargs)

    def ensure_amplify_review_source(self, request):
        source_types_added = set(self.adgroupsource_set.all().values_list("source__source_type__type", flat=True))
        if constants.SourceType.OUTBRAIN not in source_types_added:
            outbrain_source = core.source.Source.objects.get(source_type__type=constants.SourceType.OUTBRAIN)
            core.entity.AdGroupSource.objects.create(
                request,
                self,
                outbrain_source,
                write_history=False,
                k1_sync=False,
                ad_review_only=True,
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            )

    class QuerySet(models.QuerySet):
        def filter_by_user(self, user):
            if user.has_perm("zemauth.can_see_all_accounts"):
                return self
            return self.filter(
                models.Q(campaign__account__users__id=user.id) | models.Q(campaign__account__agency__users__id=user.id)
            ).distinct()

        def filter_by_agencies(self, agencies):
            if not agencies:
                return self
            return self.filter(campaign__account__agency__in=agencies)

        def filter_by_account_types(self, account_types):
            if not account_types:
                return self
            return self.filter(campaign__account__settings__account_type__in=account_types)

        def filter_by_sources(self, sources):
            # FIXME:circular dependency
            import core.entity.settings

            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(adgroupsource__source__in=sources).distinct()

        def exclude_archived(self, show_archived=False):
            if show_archived:
                return self
            return self.exclude(settings__archived=True)

        def filter_running(self, date=None):
            """
            This function checks if adgroup is running on arbitrary number of adgroups
            with a fixed amount of queries.
            An adgroup is running if:
                - it was set as active(adgroupsettings)
                - current date is between start and stop(flight time)
            """
            if not date:
                date = dates_helper.local_today()
            return self.filter(
                settings__state=constants.AdGroupSettingsState.ACTIVE, settings__start_date__lte=date
            ).exclude(settings__end_date__isnull=False, settings__end_date__lt=date)

        def filter_active(self):
            """
            Returns only ad groups that have settings set to active.
            """
            return self.filter(settings__state=constants.AdGroupSettingsState.ACTIVE)
