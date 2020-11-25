import newrelic.agent
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.template.defaultfilters import pluralize
from django.utils.safestring import mark_safe

import core.features.deals
import core.features.history
import core.models.helpers
import dash.constants
import dash.features.custom_flags
import utils.dates_helper
import utils.json_helper
from utils import k1_helper


class AdGroupInstanceMixin:
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/"

    def admin_link(self):
        if self.id:
            return mark_safe('<a href="/admin/dash/adgroup/%d/">Edit</a>' % self.id)
        else:
            return "N/A"

    admin_link.allow_tags = True

    def get_sspd_url(self):
        if self.id:
            return settings.SSPD_AD_GROUP_REDIRECT_URL.format(id=self.id)
        else:
            return "N/A"

    @newrelic.agent.function_trace()
    def get_current_settings(self):
        return self.settings

    def can_restore(self):
        if self.campaign.is_archived():
            return False

        return True

    def is_archived(self):
        return self.archived

    @transaction.atomic
    def archive(self, request):
        self.settings.update(request, archived=True)

    @transaction.atomic
    def restore(self, request):
        self.settings.update(request, archived=False)

    def is_blocked_by_custom_flag(self):
        return bool(self.get_all_custom_flags().get(dash.features.custom_flags.constants.CUSTOMER_BLOCKED))

    @property
    def is_disabled(self):
        return self.campaign.account.is_disabled

    @classmethod
    def get_running_status(cls, ad_group_settings):
        """
        Returns the actual running status of ad group settings with selected sources settings.
        """

        if not cls.is_ad_group_active(ad_group_settings):
            return dash.constants.AdGroupRunningStatus.INACTIVE

        if cls.get_running_status_by_flight_time(ad_group_settings) == dash.constants.AdGroupRunningStatus.ACTIVE:
            return dash.constants.AdGroupRunningStatus.ACTIVE

        return dash.constants.AdGroupRunningStatus.INACTIVE

    def get_sources_state(self):
        # FIXME:circular dependency
        import core.models.settings

        settings = self.get_current_settings()

        ad_group_source_settings = (
            core.models.settings.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=self)
            .group_current_settings()
            .values("ad_group_source__source_id", "state")
        )

        states = {}
        for source_settings in ad_group_source_settings:
            state = source_settings["state"]
            if state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
                state = settings.state

            states[source_settings["ad_group_source__source_id"]] = state

        return states

    @classmethod
    def get_running_status_by_flight_time(cls, ad_group_settings):
        if not cls.is_ad_group_active(ad_group_settings):
            return dash.constants.AdGroupRunningStatus.INACTIVE

        now = utils.dates_helper.local_today()
        if ad_group_settings.start_date <= now and (
            ad_group_settings.end_date is None or now <= ad_group_settings.end_date
        ):
            return dash.constants.AdGroupRunningStatus.ACTIVE
        return dash.constants.AdGroupRunningStatus.INACTIVE

    @classmethod
    def get_running_status_by_sources_setting(cls, ad_group_settings, ad_group_sources_settings):
        """
        Returns "running" when at least one of the ad group sources settings status is
        set to be active.
        """

        if not cls.is_ad_group_active(ad_group_settings):
            return dash.constants.AdGroupRunningStatus.INACTIVE

        if ad_group_sources_settings and any(
            x.state == dash.constants.AdGroupSourceSettingsState.ACTIVE for x in ad_group_sources_settings
        ):
            return dash.constants.AdGroupRunningStatus.ACTIVE
        return dash.constants.AdGroupRunningStatus.INACTIVE

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.campaign.account.name
        campaign_name = self.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.name
        else:
            ad_group_name = new_adgroup_name
        return "ONE: {} / {} / {} / {}".format(
            core.models.helpers.shorten_name(account_name),
            core.models.helpers.shorten_name(campaign_name),
            core.models.helpers.shorten_name(ad_group_name),
            self.id,
        )

    @classmethod
    def is_ad_group_active(cls, ad_group_settings):
        if ad_group_settings and ad_group_settings.state == dash.constants.AdGroupSettingsState.ACTIVE:
            return True
        return False

    def get_default_blacklist_name(self):
        return "Default blacklist for ad group {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return "Default whitelist for ad group {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return dash.constants.PublisherBlacklistLevel.ADGROUP

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

        self.write_history(
            changes_text, user=request.user if request else None, action_type=dash.constants.HistoryActionType.CREATE
        )

    def write_history_cloned_to(self, request, destination_ad_group):
        changes_text = "This Ad group was cloned to {}".format(destination_ad_group.get_name_with_id())
        self.write_history(
            changes_text, user=request.user if request else None, action_type=dash.constants.HistoryActionType.CREATE
        )

    def write_history_cloned_from(self, request, source_ad_group):
        source_names = list(self.adgroupsource_set.all().values_list("source__name", flat=True))
        if source_names:
            changes_text = "Cloned settings and content ads from {} and automatically created campaigns for {} sources ({})".format(
                source_ad_group.get_name_with_id(), len(source_names), ", ".join(source_names)
            )
        else:
            changes_text = None

        self.write_history(changes_text, user=request.user, action_type=dash.constants.HistoryActionType.CREATE)

    def write_history_content_ads_cloned(self, request, content_ads, batch, source_ad_group, overriden_state):
        state_text = "Cloned content ads state was left intact."
        if overriden_state is not None:
            state_text = 'State of all cloned content ads was set to "{}".'.format(
                dash.constants.ContentAdSourceState.get_text(overriden_state)
            )

        changes_text = 'Cloned {} content ad{} from "{}" as batch "{}". {}'.format(
            len(content_ads), pluralize(len(content_ads)), source_ad_group.get_name_with_id(), batch.name, state_text
        )

        self.write_history(changes_text, user=request.user, action_type=dash.constants.HistoryActionType.CREATE)

    def write_history_source_added(self, request, ad_group_source):
        self.write_history(
            "{} source added".format(ad_group_source.source.name),
            user=request.user if request else None,
            action_type=dash.constants.HistoryActionType.MEDIA_SOURCE_ADD,
        )

    def write_history(self, changes_text, changes=None, user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return  # nothing to write

        campaign, account, agency = core.models.helpers.generate_parents(ad_group=self)
        history = core.features.history.History.objects.create(
            ad_group=self,
            campaign=campaign,
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=utils.json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=dash.constants.HistoryLevel.AD_GROUP,
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

    def get_all_configured_deals(self):
        return core.features.deals.DirectDealConnection.objects.filter(
            Q(adgroup=self.id)
            | Q(campaign=self.campaign)
            | Q(account=self.campaign.account)
            | Q(agency=self.campaign.account.agency, agency__isnull=False)
            | Q(agency=None, account=None, campaign=None, adgroup=None)
        )

    def get_deals(self, request):
        deals = (
            core.features.deals.DirectDeal.objects.filter(
                directdealconnection__adgroup__isnull=False, directdealconnection__adgroup__id=self.id
            )
            .select_related("source")
            .distinct()
        )

        if request and not request.user.has_perm("zemauth.can_see_internal_deals"):
            deals = deals.exclude(is_internal=True)

        return list(deals)

    def remove_deals(self, request, deals):
        self.directdealconnection_set.filter(deal__id__in=[x.id for x in deals]).delete(request=request)

    def add_deals(self, request, deals):
        for deal in deals:
            core.features.deals.DirectDealConnection.objects.create(request, deal, adgroup=self)

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user if request else None
        super().save(*args, **kwargs)

    def compute_local_daily_cap(self):
        return type(self).objects.filter(id=self.id).compute_total_local_daily_cap()

    def ensure_amplify_review_source(self, request):
        source_types_added = set(self.adgroupsource_set.all().values_list("source__source_type__type", flat=True))

        if dash.constants.SourceType.OUTBRAIN not in source_types_added:
            outbrain_source = core.models.Source.objects.get(source_type__type=dash.constants.SourceType.OUTBRAIN)
            core.models.AdGroupSource.objects.create(
                request,
                self,
                outbrain_source,
                write_history=False,
                k1_sync=False,
                ad_review_only=True,
                skip_notification=True,
                state=dash.constants.AdGroupSourceSettingsState.INACTIVE,
            )

    def update(self, request, **kwargs):
        with transaction.atomic():
            updates = self._clean_updates(kwargs)
            if not updates:
                return
            self.validate(updates, request)
            self._apply_updates_and_save(request, updates)
        k1_helper.update_ad_group(self, "Adgroup.update")

    def _clean_updates(self, updates):
        new_updates = {}

        for field, value in updates.items():
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates_and_save(self, request, updates):
        bidding_type_changed = False
        for field, value in updates.items():
            if field == "entity_tags":
                self.entity_tags.clear()
                if value:
                    self.entity_tags.add(*value)
            elif field == "bidding_type":
                if value:
                    self.bidding_type = value
                    bidding_type_changed = True
            elif field == "amplify_review":
                if value:
                    self.amplify_review = value
                    self.ensure_amplify_review_source(request)
            else:
                setattr(self, field, value)
        self.save(request)

        if bidding_type_changed:
            self.settings.apply_bids_to_sources()
