import json
import re
import logging
import decimal

from django.db import transaction
from django.db.models import Prefetch
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import models as authmodels
from django.http import Http404

from automation import autopilot_budgets, autopilot_plus, campaign_stop
from dash.views import helpers
from dash import forms
from dash import models
from dash import api
from dash import constants
from dash import retargeting_helper
from dash import campaign_goals
from dash import facebook_helper
from dash import ga_helper
from dash import content_insights_helper
from dash import cpc_constraints

from utils import api_common
from utils import exc
from utils import email_helper
from utils import k1_helper
from utils import redirector_helper

from zemauth.models import User as ZemUser


logger = logging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7
CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10


class AdGroupSettings(api_common.BaseApiView):

    def get(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = ad_group.get_current_settings()

        response = {
            'settings': self.get_dict(request, settings, ad_group),
            'default_settings': self.get_default_settings_dict(ad_group),
            'action_is_waiting': False,
            'retargetable_adgroups': self.get_retargetable_adgroups(
                request,
                ad_group,
                settings.retargeting_ad_groups + settings.exclusion_retargeting_ad_groups
            ),
            'audiences': self.get_audiences(
                request,
                ad_group,
                settings.audience_targeting + settings.exclusion_audience_targeting
            ),
            'warnings': self.get_warnings(request, settings),
            'can_archive': ad_group.can_archive(),
            'can_restore': ad_group.can_restore(),
            'archived': settings.archived,
        }
        if request.user.has_perm('zemauth.can_see_backend_hacks'):
            response['hacks'] = models.CustomHack.objects.all().filter_applied(
                ad_group=ad_group
            ).to_dict_list()

        return self.create_api_response(response)

    def put(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)
        previous_ad_group_name = ad_group.name

        current_settings = ad_group.get_current_settings()

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(ad_group, request.user, resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_ad_group(ad_group, form.cleaned_data)

        new_settings = current_settings.copy_settings()
        latest_ad_group_source_settings = models.AdGroupSourceSettings.objects.all().\
            filter(ad_group_source__ad_group=ad_group).\
            group_current_settings().\
            select_related('ad_group_source')
        self.set_settings(
            ad_group,
            latest_ad_group_source_settings,
            new_settings,
            form.cleaned_data,
            request.user
        )

        campaign_settings = ad_group.campaign.get_current_settings()

        self.validate_all_rtb_state(current_settings, new_settings)
        self.validate_yahoo_desktop_targeting(ad_group, current_settings, new_settings)
        self.validate_all_rtb_campaign_stop(ad_group, current_settings, new_settings, campaign_settings)

        # update ad group name
        current_settings.ad_group_name = previous_ad_group_name
        new_settings.ad_group_name = ad_group.name

        changes = current_settings.get_setting_changes(new_settings)
        changes, current_settings, new_settings = self.b1_sources_group_adjustments(
            changes, current_settings, new_settings)

        if new_settings.id is None or 'tracking_code' in changes:
            redirector_helper.insert_adgroup(
                ad_group,
                new_settings,
                campaign_settings,
            )
        try:
            change_b1_rtb_sources_cpcs = ('b1_sources_group_cpc_cc' in changes or
                                          changes.get('b1_sources_group_enabled'))
            helpers.adjust_adgroup_sources_cpcs(
                ad_group, new_settings,
                request.user.has_perm('zemauth.can_set_rtb_sources_as_one_cpc'),
                change_b1_rtb_sources_cpcs)
        except cpc_constraints.ValidationError as err:
            raise exc.ValidationError(errors={
                'b1_sources_group_cpc_cc': list(err)
            })
        k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettings.put')

        # save
        ad_group.save(request)
        if changes:
            new_settings.save(
                request,
                action_type=constants.HistoryActionType.SETTINGS_CHANGE)

            changes_text = models.AdGroupSettings.get_changes_text(
                current_settings, new_settings, request.user, separator='\n')

            email_helper.send_ad_group_notification_email(ad_group, request, changes_text)
            if (('autopilot_daily_budget' in changes or 'autopilot_state' in changes and
                 changes['autopilot_state'] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
                or (new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and
                    'b1_sources_group_state' in changes)):
                autopilot_plus.initialize_budget_autopilot_on_ad_group(new_settings, send_mail=True)

        response = {
            'settings': self.get_dict(request, new_settings, ad_group),
            'default_settings': self.get_default_settings_dict(ad_group),
            'action_is_waiting': False,
            'archived': new_settings.archived,
        }

        return self.create_api_response(response)

    def validate_all_rtb_state(self, settings, new_settings):
        # MVP for all-RTB-sources-as-one
        # Ensure that AdGroup is paused when enabling/disabling All RTB functionality
        # For now this is the easiest solution to avoid conflicts with ad group budgets and state validations

        if new_settings.state == constants.AdGroupSettingsState.INACTIVE:
            return

        all_rtb_enabled = settings.b1_sources_group_enabled and \
            settings.autopilot_state == constants.AdGroupSettingsAutopilotState.INACTIVE

        new_all_rtb_enabled = new_settings.b1_sources_group_enabled and \
            new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.INACTIVE

        if all_rtb_enabled != new_all_rtb_enabled:
            msg = 'To manage Daily Spend Cap for All RTB as one, ad group must be paused first.'
            if not new_all_rtb_enabled:
                'To disable managing Daily Spend Cap for All RTB as one, ad group must be paused first.'
            raise exc.ValidationError(errors={'autopilot_state': [msg]})

    def validate_all_rtb_campaign_stop(self, ad_group, current_settings, new_settings, campaign_settings):
        changes = current_settings.get_setting_changes(new_settings)
        if 'b1_sources_group_daily_budget' in changes:
            new_daily_budget = decimal.Decimal(changes['b1_sources_group_daily_budget'])
            max_daily_budget = campaign_stop.get_max_settable_b1_sources_group_budget(
                ad_group,
                ad_group.campaign,
                new_settings,
                campaign_settings,
            )
            if max_daily_budget is not None and new_daily_budget > max_daily_budget:
                raise exc.ValidationError(errors={
                    'daily_budget_cc': [
                        'Daily Spend Cap is too high. Maximum daily spend '
                        'cap can be up to ${max_daily_budget}.'.format(
                            max_daily_budget=max_daily_budget
                        )
                    ]
                })

        if 'b1_sources_group_state' in changes:
            can_enable_b1_sources_group = campaign_stop.can_enable_b1_sources_group(
                ad_group,
                ad_group.campaign,
                new_settings,
                campaign_settings,
            )
            if not can_enable_b1_sources_group:
                raise exc.ValidationError(errors={
                    'state': ['Please add additional budget to your campaign to make changes.']
                })

    def b1_sources_group_adjustments(self, changes, current_settings, new_settings):
        # Turning on RTB-as-one
        if 'b1_sources_group_enabled' in changes and changes['b1_sources_group_enabled']:
            new_b1_sources_group_cpc = constants.SourceAllRTB.DEFAULT_CPC_CC
            if changes.get('b1_sources_group_cpc_cc'):
                new_b1_sources_group_cpc = changes['b1_sources_group_cpc_cc']
            if new_settings.cpc_cc:
                new_b1_sources_group_cpc = min(new_settings.cpc_cc, new_b1_sources_group_cpc)
            new_settings.b1_sources_group_cpc_cc = new_b1_sources_group_cpc

            if changes.get('b1_sources_group_daily_budget'):
                new_settings.b1_sources_group_daily_budget = changes.get('b1_sources_group_daily_budget')
            else:
                new_settings.b1_sources_group_daily_budget = constants.SourceAllRTB.DEFAULT_DAILY_BUDGET

        # Changing adgroup max cpc
        if changes.get('cpc_cc') and new_settings.b1_sources_group_enabled:
            new_settings.b1_sources_group_cpc_cc = min(changes.get('cpc_cc'), new_settings.b1_sources_group_cpc_cc)

        return current_settings.get_setting_changes(new_settings), current_settings, new_settings

    @staticmethod
    def validate_yahoo_desktop_targeting(ad_group, settings, new_settings):
        # optimization: only check when targeting is changed to desktop only
        if not (settings.target_devices != new_settings.target_devices and
                new_settings.target_devices == [constants.AdTargetDevice.DESKTOP]):
            return

        for ags in ad_group.adgroupsource_set.all():
            if ags.source.source_type.type != constants.SourceType.YAHOO:
                continue
            curr_ags_settings = ags.get_current_settings()
            if curr_ags_settings.state != constants.AdGroupSettingsState.ACTIVE:
                continue
            min_cpc = ags.source.source_type.get_min_cpc(new_settings)
            if min_cpc and curr_ags_settings.cpc_cc < min_cpc:
                msg = 'CPC on Yahoo is too low for desktop-only targeting. Please set it to at least $0.25.'
                raise exc.ValidationError(errors={'target_devices': [msg]})

    def _supports_max_cpm(self, latest_ad_group_source_settings):
        unsupported_sources = []
        for ad_group_source_settings in latest_ad_group_source_settings:
            if ad_group_source_settings.state != constants.AdGroupSourceSettingsState.ACTIVE:
                continue

            source = ad_group_source_settings.ad_group_source.source
            if not source.can_set_max_cpm():
                unsupported_sources.append(source)

        return unsupported_sources

    def get_warnings(self, request, ad_group_settings):
        warnings = {}

        ad_group = ad_group_settings.ad_group
        latest_ad_group_source_settings = models.AdGroupSourceSettings.objects.all().\
            filter(ad_group_source__ad_group=ad_group).\
            group_current_settings().\
            select_related('ad_group_source__source')

        supports_retargeting, unsupported_sources =\
            retargeting_helper.supports_retargeting(latest_ad_group_source_settings)
        if not supports_retargeting:
            retargeting_warning = {
                'sources': [s.name for s in unsupported_sources]
            }
            warnings['retargeting'] = retargeting_warning

        if ad_group_settings.landing_mode:
            warnings['end_date'] = {
                'campaign_id': ad_group_settings.ad_group.campaign.id,
            }

        max_cpm_unsupported_sources = self._supports_max_cpm(latest_ad_group_source_settings)
        if max_cpm_unsupported_sources:
            warnings['max_cpm'] = {'sources': [s.name for s in max_cpm_unsupported_sources]}

        return warnings

    def get_dict(self, request, settings, ad_group):
        result = {}

        if settings:
            primary_campaign_goal = campaign_goals.get_primary_campaign_goal(ad_group.campaign)
            result = {
                'id': str(ad_group.pk),
                'campaign_id': str(ad_group.campaign_id),
                'name': ad_group.name,
                'state': settings.state,
                'start_date': settings.start_date,
                'end_date': settings.end_date,
                'cpc_cc':
                    '{:.3f}'.format(settings.cpc_cc)
                    if settings.cpc_cc is not None else '',
                'max_cpm':
                    '{:.3f}'.format(settings.max_cpm)
                    if settings.max_cpm is not None else '',
                'daily_budget_cc':
                    '{:.2f}'.format(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None else '',
                'target_devices': settings.target_devices,
                'target_regions': settings.target_regions,
                'tracking_code': settings.tracking_code,
                'autopilot_state': settings.autopilot_state,
                'autopilot_daily_budget':
                    '{:.2f}'.format(settings.autopilot_daily_budget)
                    if settings.autopilot_daily_budget is not None else '',
                'retargeting_ad_groups': settings.retargeting_ad_groups,
                'exclusion_retargeting_ad_groups': settings.exclusion_retargeting_ad_groups,
                'notes': settings.notes,
                'bluekai_targeting': settings.bluekai_targeting,
                'interest_targeting': settings.interest_targeting,
                'exclusion_interest_targeting': settings.exclusion_interest_targeting,
                'audience_targeting': settings.audience_targeting,
                'exclusion_audience_targeting': settings.exclusion_audience_targeting,
                'redirect_pixel_urls': settings.redirect_pixel_urls,
                'redirect_javascript': settings.redirect_javascript,
                'autopilot_min_budget': autopilot_budgets.get_adgroup_minimum_daily_budget(ad_group),
                'autopilot_optimization_goal': primary_campaign_goal.type if primary_campaign_goal else None,
                'dayparting': settings.dayparting,
                'b1_sources_group_enabled': settings.b1_sources_group_enabled,
                'b1_sources_group_daily_budget': settings.b1_sources_group_daily_budget,
                'b1_sources_group_cpc_cc': settings.b1_sources_group_cpc_cc,
                'b1_sources_group_state': settings.b1_sources_group_state,
                'whitelist_publisher_groups': settings.whitelist_publisher_groups,
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, ad_group, latest_ad_group_source_settings, settings, resource, user):
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.interest_targeting = resource['interest_targeting']
        settings.exclusion_interest_targeting = resource['exclusion_interest_targeting']
        settings.ad_group_name = resource['name']
        settings.tracking_code = resource['tracking_code']
        settings.dayparting = resource['dayparting']

        if user.has_perm('zemauth.can_set_ad_group_max_cpc'):
            settings.cpc_cc = resource['cpc_cc']

        if user.has_perm('zemauth.can_set_ad_group_max_cpm'):
            settings.max_cpm = resource['max_cpm']

        if not settings.landing_mode and user.has_perm('zemauth.can_set_adgroup_to_auto_pilot'):
            settings.autopilot_state = resource['autopilot_state']
            if resource['autopilot_state'] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                settings.autopilot_daily_budget = resource['autopilot_daily_budget']

        if user.has_perm('zemauth.can_view_retargeting_settings') and\
                retargeting_helper.supports_retargeting(latest_ad_group_source_settings):
            settings.retargeting_ad_groups = resource['retargeting_ad_groups']

        if user.has_perm('zemauth.can_target_custom_audiences') and\
                retargeting_helper.supports_retargeting(latest_ad_group_source_settings):
            settings.exclusion_retargeting_ad_groups = resource['exclusion_retargeting_ad_groups']
            settings.audience_targeting = resource['audience_targeting']
            settings.exclusion_audience_targeting = resource['exclusion_audience_targeting']

        # TODO(nsaje): protect with permission?
        settings.b1_sources_group_enabled = resource['b1_sources_group_enabled']
        settings.b1_sources_group_daily_budget = resource['b1_sources_group_daily_budget']
        settings.b1_sources_group_state = resource['b1_sources_group_state']
        if user.has_perm('zemauth.can_set_rtb_sources_as_one_cpc') and settings.b1_sources_group_enabled:
            settings.b1_sources_group_cpc_cc = resource['b1_sources_group_cpc_cc']

        settings.bluekai_targeting = resource['bluekai_targeting']

        if user.has_perm('zemauth.can_set_white_blacklist_publisher_groups'):
            settings.whitelist_publisher_groups = resource['whitelist_publisher_groups']

    def get_default_settings_dict(self, ad_group):
        settings = ad_group.campaign.get_current_settings()

        return {
            'target_devices': settings.target_devices,
            'target_regions': settings.target_regions
        }

    def get_retargetable_adgroups(self, request, ad_group, existing_targetings):
        '''
        Get adgroups that can retarget this adgroup
        '''
        if not request.user.has_perm('zemauth.can_view_retargeting_settings'):
            return []

        account = ad_group.campaign.account

        ad_groups = models.AdGroup.objects.filter(
            campaign__account=account
        ).select_related('campaign').order_by('id')

        ad_group_settings = models.AdGroupSettings.objects.all().filter(
            ad_group__campaign__account=account
        ).group_current_settings().values_list('ad_group__id', 'archived')
        archived_map = {adgs[0]: adgs[1] for adgs in ad_group_settings}

        if request.user.has_perm('zemauth.can_target_custom_audiences'):
            result = [{
                'id': adg.id,
                'name': adg.name,
                'archived': archived_map.get(adg.id) or False,
                'campaign_name': adg.campaign.name,
            } for adg in ad_groups if not archived_map.get(adg.id) or adg.id in existing_targetings]
        else:
            result = [{
                'id': adg.id,
                'name': adg.name,
                'archived': archived_map.get(adg.id) or False,
                'campaign_name': adg.campaign.name,
            } for adg in ad_groups]

        return result

    def get_audiences(self, request, ad_group, existing_targetings):
        if not request.user.has_perm('zemauth.can_target_custom_audiences'):
            return []

        audiences = models.Audience.objects.\
            filter(pixel__account_id=ad_group.campaign.account.pk).\
            filter(Q(archived=False) | Q(pk__in=existing_targetings)).\
            order_by('name')

        return [
            {
                'id': audience.pk,
                'name': audience.name,
                'archived': audience.archived or False,
            }
            for audience in audiences
        ]


class AdGroupSettingsState(api_common.BaseApiView):

    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_control_ad_group_state_in_table'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        current_settings = ad_group.get_current_settings()
        return self.create_api_response({
            'id': str(ad_group.pk),
            'state': current_settings.state,
        })

    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_control_ad_group_state_in_table'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)
        data = json.loads(request.body)
        new_state = data.get('state')

        campaign_settings = ad_group.campaign.get_current_settings()
        helpers.validate_ad_groups_state([ad_group], ad_group.campaign, campaign_settings, new_state)

        changed = ad_group.set_state(request, new_state)
        if changed:
            k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettingsState.post')

        return self.create_api_response({
            'id': str(ad_group.pk),
            'state': new_state,
        })


class CampaignGoalValidation(api_common.BaseApiView):

    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.can_see_campaign_goals'):
            raise exc.MissingDataError()
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_goal = json.loads(request.body)
        goal_form = forms.CampaignGoalForm(campaign_goal, campaign_id=campaign.pk)

        errors = {}
        result = {}
        if not goal_form.is_valid():
            errors.update(dict(goal_form.errors))

        if campaign_goal['type'] == constants.CampaignGoalKPI.CPA:
            if not campaign_goal.get('id'):
                conversion_form = forms.ConversionGoalForm(
                    campaign_goal.get('conversion_goal', {}),
                    campaign_id=campaign.pk,
                )
                if conversion_form.is_valid():
                    result['conversion_goal'] = conversion_form.cleaned_data
                else:
                    errors['conversion_goal'] = conversion_form.errors

        if errors:
            raise exc.ValidationError(errors=errors)

        return self.create_api_response(result)


class CampaignSettings(api_common.BaseApiView):

    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        response = {
            'settings': self.get_dict(request, campaign_settings, campaign),
            'can_archive': campaign.can_archive(),
            'can_restore': campaign.can_restore(),
            'archived': campaign_settings.archived,
        }
        if request.user.has_perm('zemauth.can_modify_campaign_manager'):
            response['campaign_managers'] = self.get_campaign_managers(request, campaign, campaign_settings)

        if request.user.has_perm('zemauth.can_see_campaign_goals'):
            response['goals'] = self.get_campaign_goals(
                campaign
            )
        if request.user.has_perm('zemauth.can_see_backend_hacks'):
            response['hacks'] = models.CustomHack.objects.all().filter_applied(
                campaign=campaign
            ).to_dict_list()

        return self.create_api_response(response)

    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        resource = json.loads(request.body)

        settings_dict = resource.get('settings', {})

        current_settings = campaign.get_current_settings()
        new_settings = current_settings.copy_settings()

        settings_form = forms.CampaignSettingsForm(settings_dict)
        errors = {}
        if not settings_form.is_valid():
            errors.update(dict(settings_form.errors))

        current = models.CampaignGoal.objects.filter(campaign=campaign)
        changes = resource.get('goals', {
            'added': [],
            'removed': [],
            'primary': None,
            'modified': {}
        })

        # If the view is used via a REST API proxy, don't require goals to be already defined,
        # since that produces a chicken-and-egg problem. REST API combines POST and PUT calls into one
        # on campaign creation and thus can't have campaign goals created yet.
        if not self.rest_proxy and len(current) - len(changes['removed']) + len(changes['added']) <= 0:
            errors['no_goals'] = 'At least one goal must be defined'
            raise exc.ValidationError(errors=errors)

        with transaction.atomic():
            goal_errors = self.set_goals(request, campaign, changes)

        if any(goal_error for goal_error in goal_errors):
            errors['goals'] = goal_errors

        if errors:
            raise exc.ValidationError(errors=errors)

        self.set_settings(request, new_settings, campaign, settings_form.cleaned_data)
        self.set_campaign(campaign, settings_form.cleaned_data)

        if current_settings.get_setting_changes(new_settings):
            helpers.save_campaign_settings_and_propagate(campaign, current_settings, new_settings, request)
            helpers.log_and_notify_campaign_settings_change(
                campaign, current_settings, new_settings, request
            )
            if (current_settings.ga_property_id != new_settings.ga_property_id and
                    new_settings.enable_ga_tracking and
                    new_settings.ga_property_id):
                try:
                    is_readable = ga_helper.is_readable(new_settings.ga_property_id)
                except:
                    is_readable = False
                if not is_readable:
                    email_helper.send_ga_setup_instructions(request.user)

        response = {
            'settings': self.get_dict(request, new_settings, campaign),
            'archived': new_settings.archived,
        }

        if request.user.has_perm('zemauth.can_see_campaign_goals'):
            response['goals'] = self.get_campaign_goals(campaign)

        return self.create_api_response(response)

    def set_goals(self, request, campaign, changes):
        if not request.user.has_perm('zemauth.can_see_campaign_goals'):
            return []

        new_primary_id = None
        errors = []
        for goal in changes['added']:
            is_primary = goal['primary']

            goal['primary'] = False

            if goal.get('conversion_goal'):
                conversion_form = forms.ConversionGoalForm(
                    {
                        'type': goal['conversion_goal'].get('type'),
                        'conversion_window': goal['conversion_goal'].get('conversion_window'),
                        'goal_id': goal['conversion_goal'].get('goal_id'),
                    },
                    campaign_id=campaign.pk,
                )
                errors.append(dict(conversion_form.errors))
                conversion_goal, goal_added = campaign_goals.create_conversion_goal(
                    request,
                    conversion_form,
                    campaign,
                    value=goal['value']
                )

            else:
                goal_form = forms.CampaignGoalForm(goal, campaign_id=campaign.pk)
                errors.append(dict(goal_form.errors))
                goal_added = campaign_goals.create_campaign_goal(
                    request, goal_form, campaign, value=goal['value']
                )

            if is_primary:
                new_primary_id = goal_added.pk

            campaign_goals.add_campaign_goal_value(
                request, goal_added, goal['value'], campaign, skip_history=True
            )

        for goal_id, value in changes['modified'].iteritems():
            goal = models.CampaignGoal.objects.get(pk=goal_id)
            campaign_goals.add_campaign_goal_value(request, goal, value, campaign)

        removed_goals = {goal['id'] for goal in changes['removed']}
        for goal_id in removed_goals:
            campaign_goals.delete_campaign_goal(request, goal_id, campaign)

        new_primary_id = new_primary_id or changes['primary']
        if new_primary_id and new_primary_id not in removed_goals:
            try:
                campaign_goals.set_campaign_goal_primary(request, campaign, new_primary_id)
            except exc.ValidationError as error:
                errors.append(str(error))

        return errors

    def get_campaign_goals(self, campaign):
        ret = []
        goals = models.CampaignGoal.objects.filter(
            campaign=campaign
        ).prefetch_related(
            Prefetch(
                'values',
                queryset=models.CampaignGoalValue.objects.order_by(
                    'created_dt'
                )
            )
        ).select_related('conversion_goal').order_by('id')

        for campaign_goal in goals:
            goal_blob = campaign_goal.to_dict(with_values=True)
            conversion_goal = campaign_goal.conversion_goal
            if conversion_goal is not None and\
                    conversion_goal.type == constants.ConversionGoalType.PIXEL:
                goal_blob['conversion_goal']['pixel_url'] = conversion_goal.pixel.get_url()
            ret.append(goal_blob)
        return ret

    def get_dict(self, request, settings, campaign):
        if not settings:
            return {}

        result = {
            'id': str(campaign.pk),
            'account_id': str(campaign.account_id),
            'name': campaign.name,
            'campaign_goal': settings.campaign_goal,
            'goal_quantity': settings.goal_quantity,
            'enable_ga_tracking': settings.enable_ga_tracking,
            'ga_property_id': settings.ga_property_id,
            'ga_tracking_type': settings.ga_tracking_type,
            'enable_adobe_tracking': settings.enable_adobe_tracking,
            'adobe_tracking_param': settings.adobe_tracking_param,
        }

        result['target_devices'] = settings.target_devices
        result['target_regions'] = settings.target_regions

        if request.user.has_perm('zemauth.can_modify_campaign_manager'):
            result['campaign_manager'] = str(settings.campaign_manager.id)\
                if settings.campaign_manager is not None else None

        if request.user.has_perm('zemauth.can_modify_campaign_iab_category'):
            result['iab_category'] = settings.iab_category

        if settings.enable_ga_tracking and settings.ga_property_id:
            try:
                result['ga_property_readable'] = ga_helper.is_readable(settings.ga_property_id)
            except:
                logger.exception("Google Analytics validation failed")

        return result

    def set_settings(self, request, settings, campaign, resource):
        settings.name = resource['name']
        settings.campaign_goal = resource['campaign_goal']
        settings.goal_quantity = resource['goal_quantity']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.enable_ga_tracking = resource['enable_ga_tracking']
        settings.enable_adobe_tracking = resource['enable_adobe_tracking']
        settings.adobe_tracking_param = resource['adobe_tracking_param']
        if request.user.has_perm('zemauth.can_modify_campaign_manager'):
            settings.campaign_manager = resource['campaign_manager']
        if request.user.has_perm('zemauth.can_modify_campaign_iab_category'):
            settings.iab_category = resource['iab_category']
        if settings.enable_ga_tracking and request.user.has_perm('zemauth.can_set_ga_api_tracking'):
            settings.ga_tracking_type = resource['ga_tracking_type']

            if settings.ga_tracking_type == constants.GATrackingType.API:
                settings.ga_property_id = resource['ga_property_id']

    def set_campaign(self, campaign, resource):
        campaign.name = resource['name']

    def get_campaign_managers(self, request, campaign, settings):
        users = helpers.get_users_for_manager(request.user, campaign.account, settings.campaign_manager)
        return [{'id': str(user.id),
                 'name': helpers.get_user_full_name_or_email(user)} for user in users]


class ConversionPixel(api_common.BaseApiView):

    def get(self, request, account_id):
        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)

        audience_enabled_only = request.GET.get('audience_enabled_only', '') == '1'

        pixels = models.ConversionPixel.objects.filter(account=account)
        if audience_enabled_only:
            pixels = pixels.filter(audience_enabled=True)

        rows = [self._format_pixel(pixel, request.user) for pixel in pixels]

        return self.create_api_response({
            'rows': rows,
            'conversion_pixel_tag_prefix': settings.CONVERSION_PIXEL_PREFIX + str(account.id) + '/',
        })

    def post(self, request, account_id):
        account_id = int(account_id)

        account = helpers.get_account(request.user, account_id)  # check access to account

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        name = data.get('name')
        resource = {'name': name, 'audience_enabled': data.get('audience_enabled')}

        form = forms.ConversionPixelForm(resource)
        if not form.is_valid():
            raise exc.ValidationError(message=' '.join(dict(form.errors)['name']))

        try:
            models.ConversionPixel.objects.get(account_id=account_id, name=name)
            raise exc.ValidationError(message='Conversion pixel with this name already exists.')
        except models.ConversionPixel.DoesNotExist:
            pass

        with transaction.atomic():
            conversion_pixel = models.ConversionPixel.objects.create(
                account_id=account_id,
                name=name,
                audience_enabled=form.cleaned_data['audience_enabled'] or False
            )

            # This check is done after insertion because we use READ COMMITED
            # isolation level.
            if conversion_pixel.audience_enabled:
                audience_pixels = models.ConversionPixel.objects.\
                    filter(account_id=account_id).\
                    filter(audience_enabled=True).\
                    exclude(pk=conversion_pixel.id)
                if audience_pixels:
                    msg = (
                        "This pixel cannot be used for building custom audiences "
                        "because another pixel is already used: {}."
                    ).format(audience_pixels[0].name)
                    raise exc.ValidationError(errors={'audience_enabled': msg})

                k1_helper.update_account(account_id)

            changes_text = u'Added conversion pixel named {}.'.format(name)
            account.write_history(
                changes_text,
                user=request.user,
                action_type=constants.HistoryActionType.CONVERSION_PIXEL_CREATE)

        email_helper.send_account_pixel_notification(account, request)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def put(self, request, conversion_pixel_id):
        try:
            conversion_pixel = models.ConversionPixel.objects.get(id=conversion_pixel_id)
        except models.ConversionPixel.DoesNotExist:
            raise exc.MissingDataError('Conversion pixel does not exist')

        try:
            account = helpers.get_account(request.user, conversion_pixel.account_id)  # check access to account
        except exc.MissingDataError:
            raise exc.MissingDataError('Conversion pixel does not exist')

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        form = forms.ConversionPixelForm(data)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        with transaction.atomic():
            self._write_audience_enabled_change_to_history(
                request, account, conversion_pixel, form.cleaned_data)
            conversion_pixel.audience_enabled = form.cleaned_data['audience_enabled']

            if 'archived' in form.cleaned_data and request.user.has_perm('zemauth.archive_restore_entity'):
                self._write_archived_change_to_history(
                    request, account, conversion_pixel, form.cleaned_data)
                conversion_pixel.archived = form.cleaned_data['archived']

                if conversion_pixel.audience_enabled and conversion_pixel.archived:
                    raise exc.ValidationError(
                        errors={'audience_enabled': 'Cannot archive pixel used for building custom audiences.'})

            self._write_name_change_to_history(
                request, account, conversion_pixel, form.cleaned_data)

            conversion_pixel.name = form.cleaned_data['name']
            conversion_pixel.save()

            # This check is done after insertion because we use READ COMMITED
            # isolation level.
            if conversion_pixel.audience_enabled:
                audience_pixels = models.ConversionPixel.objects.\
                    filter(account_id=conversion_pixel.account_id).\
                    filter(audience_enabled=True).\
                    exclude(pk=conversion_pixel.id)
                if audience_pixels:
                    msg = "This pixel cannot be used for building custom audiences because another pixel is already used: {}.".format(audience_pixels[
                                                                                                                                      0].name)
                    raise exc.ValidationError(errors={'audience_enabled': msg})

                k1_helper.update_account(conversion_pixel.account.id)
                self._r1_upsert_audiences(conversion_pixel)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def _r1_upsert_audiences(self, conversion_pixel):
        audiences = models.Audience.objects.\
            filter(pixel_id=conversion_pixel.id).\
            filter(archived=False)
        for audience in audiences:
            redirector_helper.upsert_audience(audience)

    def _write_archived_change_to_history(self, request, account, conversion_pixel, data):
        if data['archived'] == conversion_pixel.archived:
            return

        changes_text = u'{} conversion pixel named {}.'.format(
            'Archived' if data['archived'] else 'Restored',
            conversion_pixel.name
        )
        account.write_history(
            changes_text,
            user=request.user,
            action_type=constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE
        )

    def _write_name_change_to_history(self, request, account, conversion_pixel, data):
        if data['name'] == conversion_pixel.name:
            return

        changes_text = u'Renamed conversion pixel named {} to {}.'.format(
            conversion_pixel.name,
            data['name']
        )
        account.write_history(
            changes_text,
            user=request.user,
            action_type=constants.HistoryActionType.CONVERSION_PIXEL_RENAME
        )

    def _write_audience_enabled_change_to_history(self, request, account, conversion_pixel, data):
        if data['audience_enabled'] and not conversion_pixel.audience_enabled:
            change_text = u'Pixel {} enabled for building audiences'.format(data['name'])
            account.write_history(change_text,
                                  user=request.user,
                                  action_type=constants.HistoryActionType.CONVERSION_PIXEL_AUDIENCE_ENABLED)

    def _format_pixel(self, pixel, user):
        data = {
            'id': pixel.id,
            'name': pixel.name,
            'url': pixel.get_url(),
            'audience_enabled': pixel.audience_enabled,
            'archived': pixel.archived
        }
        if user.has_perm('zemauth.can_see_pixel_traffic'):
            data['last_triggered'] = pixel.last_triggered
            data['impressions'] = pixel.impressions
        return data


class AccountSettings(api_common.BaseApiView):

    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        response = {
            'settings': self.get_dict(request, account_settings, account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
            'archived': account_settings.archived,
        }

        self._add_agencies(request, response)

        if request.user.has_perm('zemauth.can_modify_account_manager'):
            response['account_managers'] = self.get_account_managers(request, account, account_settings)

        if request.user.has_perm('zemauth.can_set_account_sales_representative'):
            response['sales_reps'] = self.get_sales_representatives()
        if request.user.has_perm('zemauth.can_see_backend_hacks'):
            response['hacks'] = models.CustomHack.objects.all().filter_applied(
                account=account
            ).to_dict_list()

        return self.create_api_response(response)

    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.AccountSettingsForm(resource.get('settings', {}))
        settings = self.save_settings(request, account, form)
        response = {
            'settings': self.get_dict(request, settings, account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
        }

        self._add_agencies(request, response)

        return self.create_api_response(response)

    def _add_agencies(self, request, response):
        if request.user.has_perm('zemauth.can_set_agency_for_account'):
            response['agencies'] = list(models.Agency.objects.all().values(
                'name',
                'sales_representative',
                'default_account_type',
            ))

    def save_settings(self, request, account, form):
        with transaction.atomic():
            # Form is additionally validated in self.set_allowed_sources method
            if not form.is_valid():
                data = self.get_validation_error_data(request, account)
                raise exc.ValidationError(errors=dict(form.errors), data=data)

            self._validate_essential_account_settings(request.user, form)

            self.set_account(request, account, form.cleaned_data)

            settings = account.get_current_settings().copy_settings()
            self.set_settings(settings, account, form.cleaned_data)

            if 'allowed_sources' in form.cleaned_data and\
                    form.cleaned_data['allowed_sources'] is not None and\
                    not request.user.has_perm('zemauth.can_modify_allowed_sources'):
                raise exc.AuthorizationError()

            if 'account_type' in form.cleaned_data and form.cleaned_data['account_type']:
                if not request.user.has_perm('zemauth.can_modify_account_type'):
                    raise exc.AuthorizationError()
                settings.account_type = form.cleaned_data['account_type']

            # FIXME: changes_text should be part of account settings comparison in
            # dash.models and not in views
            changes_text = None
            if 'allowed_sources' in form.cleaned_data and\
                    form.cleaned_data['allowed_sources'] is not None:
                changes_text = self.set_allowed_sources(
                    settings,
                    account,
                    request.user.has_perm('zemauth.can_see_all_available_sources'),
                    form
                )

            if 'facebook_page' in form.data:
                if not request.user.has_perm('zemauth.can_modify_facebook_page'):
                    raise exc.AuthorizationError()
                facebook_account = self.get_or_create_facebook_account(account)
                self.set_facebook_page(facebook_account, form)
                facebook_account.save()

            account.save(request)
            settings.save(
                request,
                action_type=constants.HistoryActionType.SETTINGS_CHANGE,
                changes_text=changes_text)
            return settings

    def _validate_essential_account_settings(self, user, form):
        if 'default_sales_representative' in form.cleaned_data and\
                form.cleaned_data['default_sales_representative'] is not None and\
                not user.has_perm('zemauth.can_set_account_sales_representative'):
            raise exc.AuthorizationError()

        if 'name' in form.cleaned_data and\
                form.cleaned_data['name'] is not None and\
                not user.has_perm('zemauth.can_modify_account_name'):
            raise exc.AuthorizationError()

        if 'default_account_manager' in form.cleaned_data and \
                form.cleaned_data['default_account_manager'] is not None and\
                not user.has_perm('zemauth.can_modify_account_manager'):
            raise exc.AuthorizationError()

    def get_validation_error_data(self, request, account):
        data = {}
        if not request.user.has_perm('zemauth.can_modify_allowed_sources'):
            return data

        data['allowed_sources'] = self.get_allowed_sources(
            request.user.has_perm('zemauth.can_see_all_available_sources'),
            [source.id for source in account.allowed_sources.all()]
        )
        return data

    def set_account(self, request, account, resource):
        if resource['name']:
            account.name = resource['name']
        if resource['agency']:
            if not request.user.has_perm('zemauth.can_set_agency_for_account'):
                raise exc.AuthorizationError()

            try:
                agency = models.Agency.objects.get(name=resource['agency'])
                account.agency = agency
            except models.Agency.DoesNotExist:
                agency = models.Agency(
                    name=resource['agency'],
                    sales_representative=resource['default_sales_representative'],
                )
                agency.save(request)
                account.agency = agency

    def get_non_removable_sources(self, account, sources_to_be_removed):
        non_removable_source_ids_list = []

        for campaign in models.Campaign.objects.filter(account_id=account.id).exclude_archived():

            for adgroup in campaign.adgroup_set.all():
                adgroup_settings = adgroup.get_current_settings()
                if adgroup_settings.state == constants.AdGroupSettingsState.INACTIVE:
                    continue

                for adgroup_source in adgroup.adgroupsource_set.filter(source__in=sources_to_be_removed):
                    adgroup_source_settings = adgroup_source.get_current_settings()
                    if adgroup_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
                        non_removable_source_ids_list.append(adgroup_source.source_id)

        return non_removable_source_ids_list

    def add_error_to_account_agency_form(self, form, to_be_removed):
        source_names = [source.name for source in models.Source.objects.filter(id__in=to_be_removed).order_by('id')]
        media_sources = ', '.join(source_names)
        if len(source_names) > 1:
            msg = 'Can\'t save changes because media sources {} are still used on this account.'.format(media_sources)
        else:
            msg = 'Can\'t save changes because media source {} is still used on this account.'.format(media_sources)

        form.add_error('allowed_sources', msg)

    def set_allowed_sources(self, settings, account, can_see_all_available_sources, account_agency_form):
        allowed_sources_dict = account_agency_form.cleaned_data.get('allowed_sources')

        if not allowed_sources_dict:
            return

        all_available_sources = self.get_all_media_sources(can_see_all_available_sources)
        current_allowed_sources = self.get_allowed_media_sources(account, can_see_all_available_sources)
        new_allowed_sources = self.filter_allowed_sources_dict(all_available_sources, allowed_sources_dict)

        new_allowed_sources_set = set(new_allowed_sources)
        current_allowed_sources_set = set(current_allowed_sources)

        to_be_removed = current_allowed_sources_set.difference(new_allowed_sources_set)
        to_be_added = new_allowed_sources_set.difference(current_allowed_sources_set)

        non_removable_sources = self.get_non_removable_sources(account, to_be_removed)
        if len(non_removable_sources) > 0:
            self.add_error_to_account_agency_form(account_agency_form, non_removable_sources)
            return

        changes_text = None
        if to_be_added or to_be_removed:
            changes_text = self.get_changes_text_for_media_sources(to_be_added, to_be_removed)
            account.allowed_sources.add(*list(to_be_added))
            account.allowed_sources.remove(*list(to_be_removed))
        return changes_text

    def get_or_create_facebook_account(self, account):
        try:
            facebook_account = account.facebookaccount
        except models.FacebookAccount.DoesNotExist:
            facebook_account = models.FacebookAccount.objects.create(
                account=account,
                status=constants.FacebookPageRequestType.EMPTY,
            )
        return facebook_account

    def set_facebook_page(self, facebook_account, form):
        new_url = form.cleaned_data['facebook_page']
        credentials = facebook_helper.get_credentials()
        facebook_helper.update_facebook_account(facebook_account, new_url, credentials['business_id'],
                                                credentials['access_token'])

    def get_all_media_sources(self, can_see_all_available_sources):
        qs_sources = models.Source.objects.all()
        if not can_see_all_available_sources:
            qs_sources = qs_sources.filter(released=True)

        return list(qs_sources)

    def get_allowed_media_sources(self, account, can_see_all_available_sources):
        qs_allowed_sources = account.allowed_sources.all()
        if not can_see_all_available_sources:
            qs_allowed_sources = qs_allowed_sources.filter(released=True)

        return list(qs_allowed_sources)

    def filter_allowed_sources_dict(self, sources, allowed_sources_dict):
        allowed_sources = []
        for source in sources:
            if source.id in allowed_sources_dict:
                value = allowed_sources_dict[source.id]
                if value.get('allowed', False):
                    allowed_sources.append(source)

        return allowed_sources

    def set_settings(self, settings, account, resource):
        settings.account = account
        if resource['name']:
            settings.name = resource['name']
        if resource['default_account_manager']:
            settings.default_account_manager = resource['default_account_manager']
        if resource['default_sales_representative']:
            settings.default_sales_representative = resource['default_sales_representative']

    def get_allowed_sources(self, include_unreleased_sources, allowed_sources_ids_list):
        allowed_sources_dict = {}

        all_sources_queryset = models.Source.objects.filter(deprecated=False)
        if not include_unreleased_sources:
            all_sources_queryset = all_sources_queryset.filter(released=True)

        all_sources = list(all_sources_queryset)

        for source in all_sources:
            source_settings = {'name': source.name}
            if source.id in allowed_sources_ids_list:
                source_settings['allowed'] = True
            source_settings['released'] = source.released
            allowed_sources_dict[source.id] = source_settings

        return allowed_sources_dict

    def add_facebook_account_to_result(self, result, account):
        try:
            result['facebook_page'] = account.facebookaccount.page_url
            result['facebook_status'] = models.constants.FacebookPageRequestType.get_text(
                account.facebookaccount.status)
        except models.FacebookAccount.DoesNotExist:
            result['facebook_status'] = models.constants.FacebookPageRequestType.get_text(
                models.constants.FacebookPageRequestType.EMPTY)

    def get_dict(self, request, settings, account):
        if not settings:
            return {}

        result = {
            'id': str(account.pk),
            'archived': settings.archived,
        }
        if request.user.has_perm('zemauth.can_modify_account_name'):
            result['name'] = account.name
        if request.user.has_perm('zemauth.can_modify_account_manager'):
            result['default_account_manager'] = str(settings.default_account_manager.id) \
                if settings.default_account_manager is not None else None
        if request.user.has_perm('zemauth.can_set_account_sales_representative'):
            result['default_sales_representative'] =\
                str(settings.default_sales_representative.id) if\
                settings.default_sales_representative is not None else None
        if request.user.has_perm('zemauth.can_modify_account_type'):
            result['account_type'] = settings.account_type
        if request.user.has_perm('zemauth.can_modify_allowed_sources'):
            result['allowed_sources'] = self.get_allowed_sources(
                request.user.has_perm('zemauth.can_see_all_available_sources'),
                [source.id for source in account.allowed_sources.all()]
            )
        if request.user.has_perm('zemauth.can_modify_facebook_page'):
            self.add_facebook_account_to_result(result, account)
        if request.user.has_perm('zemauth.can_set_agency_for_account'):
            if account.agency:
                result['agency'] = account.agency.name
            else:
                result['agency'] = ''
        return result

    def get_changes_text_for_media_sources(self, added_sources, removed_sources):
        sources_text_list = []
        if added_sources:
            added_sources_names = [source.name for source in added_sources]
            added_sources_text = u'Added allowed media sources ({})'.format(', '.join(added_sources_names))
            sources_text_list.append(added_sources_text)

        if removed_sources:
            removed_sources_names = [source.name for source in removed_sources]
            removed_sources_text = u'Removed allowed media sources ({})'.format(', '.join(removed_sources_names))
            sources_text_list.append(removed_sources_text)

        return ', '.join(sources_text_list)

    def get_account_managers(self, request, account, settings):
        users = helpers.get_users_for_manager(request.user, account, settings.default_account_manager)
        return self.format_user_list(users)

    def get_sales_representatives(self):
        users = ZemUser.objects.get_users_with_perm('campaign_settings_sales_rep').filter(is_active=True)
        return self.format_user_list(users)

    def format_user_list(self, users):
        return [{'id': str(user.id), 'name': helpers.get_user_full_name_or_email(user)} for user in users]


class AccountUsers(api_common.BaseApiView):

    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        agency_users = account.agency.users.all() if account.agency else []

        users = [self._get_user_dict(u) for u in account.users.all()]
        agency_managers = [self._get_user_dict(u, agency_managers=True) for u in agency_users]

        if request.user.has_perm('zemauth.can_see_agency_managers_under_access_permissions'):
            users = agency_managers + users

        return self.create_api_response({
            'users': users,
            'agency_managers': agency_managers if account.agency else None,
        })

    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.UserForm(resource)
        is_valid = form.is_valid()

        # in case the user already exists and form contains
        # first name and last name, error is returned. In case
        # the form only contains email, user is added to the account.
        if form.cleaned_data.get('email') is None:
            self._raise_validation_error(form.errors)

        first_name = form.cleaned_data.get('first_name')
        last_name = form.cleaned_data.get('last_name')
        email = form.cleaned_data.get('email')

        try:

            user = ZemUser.objects.get(email__iexact=email)

            if (first_name == user.first_name and last_name == user.last_name)\
                    or (not first_name and not last_name):
                created = False
            else:
                self._raise_validation_error(
                    form.errors,
                    message=u'The user with e-mail {} is already registred as \"{}\". '
                            u'Please contact technical support if you want to change the user\'s '
                            u'name or leave first and last names blank if you just want to add '
                            u'access to the account for this user.'.format(user.email, user.get_full_name())
                )
        except ZemUser.DoesNotExist:
            if not is_valid:
                self._raise_validation_error(form.errors)

            user = ZemUser.objects.create_user(email, first_name=first_name, last_name=last_name)
            self._add_user_to_groups(user)
            email_helper.send_email_to_new_user(user, request)

            created = True

        # we check account for this user to prevent multiple additions
        if not len(account.users.filter(pk=user.pk)):
            account.users.add(user)

            changes_text = u'Added user {} ({})'.format(user.get_full_name(), user.email)

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = changes_text
            new_settings.save(request, changes_text=changes_text)

        return self.create_api_response(
            {'user': self._get_user_dict(user)},
            status_code=201 if created else 200
        )

    def _add_user_to_groups(self, user):
        perm = authmodels.Permission.objects.get(codename='group_new_user_add')
        groups = authmodels.Group.objects.filter(permissions=perm)
        for group in groups:
            group.user_set.add(user)

    def _raise_validation_error(self, errors, message=None):
        raise exc.ValidationError(
            errors=dict(errors),
            pretty_message=message or u'Please specify the user\'s first name, last name and email.'
        )

    def delete(self, request, account_id, user_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.MissingDataError()

        if len(account.users.filter(pk=user.pk)):
            account.users.remove(user)
            changes_text = u'Removed user {} ({})'.format(user.get_full_name(), user.email)
            account.write_history(changes_text, user=request.user)

        return self.create_api_response({
            'user_id': user.id
        })

    def _get_user_dict(self, user, agency_managers=False):
        return {
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'last_login': user.last_login.date(),
            'is_active': user.last_login != user.date_joined,
            'is_agency_manager': agency_managers,
        }


class AccountUserAction(api_common.BaseApiView):
    ACTIVATE = 'activate'
    PROMOTE = 'promote'
    DOWNGRADE = 'downgrade'

    def __init__(self):
        self.actions = {
            AccountUserAction.ACTIVATE: self._activate,
            AccountUserAction.PROMOTE: self._promote,
            AccountUserAction.DOWNGRADE: self._downgrade,
        }
        self.permissions = {
            AccountUserAction.ACTIVATE: 'zemauth.account_agency_access_permissions',
            AccountUserAction.PROMOTE: 'zemauth.can_promote_agency_managers',
            AccountUserAction.DOWNGRADE: 'zemauth.can_promote_agency_managers',
        }

    def post(self, request, account_id, user_id, action):
        if action not in self.actions:
            raise Http404('Action does not exist')

        if not request.user.has_perm(self.permissions[action]):
            raise exc.AuthorizationError()

        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.ValidationError(
                pretty_message=u'Cannot {action} nonexisting user.'.format(action=action)
            )

        account = helpers.get_account(request.user, account_id)

        self.actions[action](request, user, account)

        return self.create_api_response()

    def _activate(self, request, user, account):
        email_helper.send_email_to_new_user(user, request)

        changes_text = u'Resent activation mail {} ({})'.format(user.get_full_name(), user.email)
        account.write_history(changes_text, user=request.user)

    def _promote(self, request, user, account):
        groups = self._get_agency_manager_groups()

        self._check_is_agency_account(account)

        account.agency.users.add(user)
        account.users.remove(user)
        user.groups.add(*groups)

    def _downgrade(self, request, user, account):
        groups = self._get_agency_manager_groups()

        self._check_is_agency_account(account)

        account.agency.users.remove(user)
        account.users.add(user)
        user.groups.remove(*groups)

    def _check_is_agency_account(self, account):
        if not account.is_agency():
            raise exc.ValidationError(
                pretty_message=u'Cannot promote user on account without agency.'
            )

    def _get_agency_manager_groups(self):
        perm = authmodels.Permission.objects.get(codename='group_agency_manager_add')
        return authmodels.Group.objects.filter(permissions=perm)


class CampaignContentInsights(api_common.BaseApiView):

    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.can_view_campaign_content_insights_side_tab'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        best_performer_rows, worst_performer_rows =\
            content_insights_helper.fetch_campaign_content_ad_metrics(
                request.user,
                campaign,
                start_date,
                end_date,
            )
        return self.create_api_response({
            'summary': 'Title',
            'metric': 'CTR',
            'best_performer_rows': best_performer_rows,
            'worst_performer_rows': worst_performer_rows,
        })


class History(api_common.BaseApiView):

    def get(self, request):
        if not request.user.has_perm('zemauth.can_view_new_history_backend'):
            raise exc.AuthorizationError()
        # in case somebody wants to fetch entire history disallow it for the
        # moment
        entity_filter = self._extract_entity_filter(request)
        if not entity_filter:
            raise exc.MissingDataError()
        order = self._extract_order(request)
        response = {
            'history': self.get_history(entity_filter, order=order)
        }
        return self.create_api_response(response)

    def _extract_entity_filter(self, request):
        entity_filter = {}
        ad_group_raw = request.GET.get('ad_group')
        if ad_group_raw:
            entity_filter['ad_group'] = helpers.get_ad_group(
                request.user, int(ad_group_raw))
        campaign_raw = request.GET.get('campaign')
        if campaign_raw:
            entity_filter['campaign'] = helpers.get_campaign(
                request.user, int(campaign_raw))
        account_raw = request.GET.get('account')
        if account_raw:
            entity_filter['account'] = helpers.get_account(
                request.user, int(account_raw))
        agency_raw = request.GET.get('agency')
        if agency_raw:
            entity_filter['agency'] = helpers.get_agency(request.user, int(agency_raw))
        level_raw = request.GET.get('level')
        if level_raw and int(level_raw) in constants.HistoryLevel.get_all():
            entity_filter['level'] = int(level_raw)
        return entity_filter

    def _extract_order(self, request):
        order = ['-created_dt']
        order_raw = request.GET.get('order') or ''
        if re.match('[-]?(created_dt|created_by)', order_raw):
            order = [order_raw]
        return order

    def get_history(self, filters, order=['-created_dt']):
        history_entries = models.History.objects.filter(
            **filters
        ).order_by(*order)

        history = []
        for history_entry in history_entries:
            history.append({
                'datetime': history_entry.created_dt,
                'changed_by': history_entry.get_changed_by_text(),
                'changes_text': history_entry.changes_text,
            })
        return history


class Agencies(api_common.BaseApiView):

    def get(self, request):
        if not request.user.has_perm('zemauth.can_filter_by_agency'):
            raise exc.AuthorizationError()

        agencies = list(
            models.Agency.objects.all().filter_by_user(
                request.user
            ).values('id', 'name')
        )
        return self.create_api_response({
            'agencies': [{
                'id': str(agency['id']),
                'name': agency['name'],
            } for agency in agencies]
        })


class FacebookAccountStatus(api_common.BaseApiView):

    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        credentials = facebook_helper.get_credentials()
        try:
            pages = facebook_helper.get_all_pages(credentials['business_id'], credentials['access_token'])
            if pages is None:
                raise exc.BaseError('Error while accessing facebook page api.')
            page_status = pages.get(account.facebookaccount.page_id)
            account_status = self._get_account_status(page_status)
        except models.FacebookAccount.DoesNotExist:
            account_status = models.constants.FacebookPageRequestType.EMPTY
        except exc.BaseError:
            account_status = models.constants.FacebookPageRequestType.ERROR

        account_status_as_string = models.constants.FacebookPageRequestType.get_text(account_status)
        return self.create_api_response({
            'status': account_status_as_string
        })

    @staticmethod
    def _get_account_status(page_status):
        if page_status is None:
            return models.constants.FacebookPageRequestType.EMPTY
        elif page_status == 'CONFIRMED':
            return models.constants.FacebookPageRequestType.CONNECTED
        elif page_status == 'PENDING':
            return models.constants.FacebookPageRequestType.PENDING
        else:
            return models.constants.FacebookPageRequestType.INVALID
