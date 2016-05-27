import datetime
import json
import logging
import newrelic.agent

from collections import OrderedDict, defaultdict
from django.db import transaction
from django.db.models import Prefetch
from django.conf import settings
from django.contrib.auth import models as authmodels

from actionlog import api as actionlog_api
from actionlog import zwei_actions
from automation import autopilot_budgets, autopilot_plus, campaign_stop
from dash.views import helpers
from dash import forms
from dash import models
from dash import api
from dash import constants
from dash import validation_helpers
from dash import retargeting_helper
from dash import campaign_goals
from dash import conversions_helper
from dash import stats_helper
import automation.settings
from reports import redshift
from utils import api_common
from utils import statsd_helper
from utils import exc
from utils import email_helper
from utils import k1_helper
from utils import lc_helper

from zemauth.models import User as ZemUser


logger = logging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7


class AdGroupSettings(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = ad_group.get_current_settings()

        response = {
            'settings': self.get_dict(settings, ad_group),
            'default_settings': self.get_default_settings_dict(ad_group),
            'action_is_waiting': actionlog_api.is_waiting_for_set_actions(ad_group),
            'retargetable_adgroups': self.get_retargetable_adgroups(request, ad_group_id),
            'warnings': self.get_warnings(request, settings)
        }
        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
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
        self.set_settings(ad_group, new_settings, form.cleaned_data, request.user)

        # update ad group name
        current_settings.ad_group_name = previous_ad_group_name
        new_settings.ad_group_name = ad_group.name

        user_action_type = constants.UserActionType.SET_AD_GROUP_SETTINGS

        self._send_update_actions(ad_group, current_settings, new_settings, request)
        k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettings.put')

        changes = current_settings.get_setting_changes(new_settings)
        if changes:
            changes_text = models.AdGroupSettings.get_changes_text(
                current_settings, new_settings, request.user, separator='\n')

            email_helper.send_ad_group_notification_email(ad_group, request, changes_text)
            helpers.log_useraction_if_necessary(request, user_action_type, ad_group=ad_group)
            if 'autopilot_daily_budget' in changes or 'autopilot_state' in changes and \
                    changes['autopilot_state'] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group=ad_group, send_mail=True)

        response = {
            'settings': self.get_dict(new_settings, ad_group),
            'default_settings': self.get_default_settings_dict(ad_group),
            'action_is_waiting': actionlog_api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    def get_warnings(self, request, ad_group_settings):
        warnings = {}

        supports_retargeting, unsupported_sources =\
            retargeting_helper.supports_retargeting(
                ad_group_settings.ad_group
            )
        if not supports_retargeting:
            retargeting_warning = {
                'sources': [s.name for s in unsupported_sources]
            }
            warnings['retargeting'] = retargeting_warning

        if ad_group_settings.landing_mode:
            warnings['end_date'] = {
                'campaign_id': ad_group_settings.ad_group.campaign.id,
            }

        return warnings

    def get_dict(self, settings, ad_group):
        result = {}

        if settings:
            primary_campaign_goal = campaign_goals.get_primary_campaign_goal(ad_group.campaign)
            result = {
                'id': str(ad_group.pk),
                'name': ad_group.name,
                'state': settings.state,
                'start_date': settings.start_date,
                'end_date': settings.end_date,
                'cpc_cc':
                    '{:.3f}'.format(settings.cpc_cc)
                    if settings.cpc_cc is not None else '',
                'daily_budget_cc':
                    '{:.2f}'.format(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None else '',
                'target_devices': settings.target_devices,
                'target_regions': settings.target_regions,
                'tracking_code': settings.tracking_code,
                'enable_ga_tracking': settings.enable_ga_tracking,
                'enable_adobe_tracking': settings.enable_adobe_tracking,
                'adobe_tracking_param': settings.adobe_tracking_param,
                'autopilot_state': settings.autopilot_state,
                'autopilot_daily_budget':
                    '{:.2f}'.format(settings.autopilot_daily_budget)
                    if settings.autopilot_daily_budget is not None else '',
                'retargeting_ad_groups': settings.retargeting_ad_groups,
                'autopilot_min_budget': autopilot_budgets.get_adgroup_minimum_daily_budget(ad_group),
                'autopilot_optimization_goal': primary_campaign_goal.type if primary_campaign_goal else None
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, ad_group, settings, resource, user):
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.ad_group_name = resource['name']

        if user.has_perm('zemauth.can_set_ad_group_max_cpc'):
            settings.cpc_cc = resource['cpc_cc']

        if user.has_perm('zemauth.can_toggle_ga_performance_tracking'):
            settings.enable_ga_tracking = resource['enable_ga_tracking']
            settings.tracking_code = resource['tracking_code']

        if user.has_perm('zemauth.can_toggle_adobe_performance_tracking'):
            settings.enable_adobe_tracking = resource['enable_adobe_tracking']
            settings.adobe_tracking_param = resource['adobe_tracking_param']

        if not settings.landing_mode and user.has_perm('zemauth.can_set_adgroup_to_auto_pilot'):
            settings.autopilot_state = resource['autopilot_state']
            if resource['autopilot_state'] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                settings.autopilot_daily_budget = resource['autopilot_daily_budget']

        if user.has_perm('zemauth.can_view_retargeting_settings') and\
                retargeting_helper.supports_retargeting(ad_group):
            settings.retargeting_ad_groups = resource['retargeting_ad_groups']

    def _send_update_actions(self, ad_group, current_settings, new_settings, request):
        actionlogs_to_send = []

        with transaction.atomic():
            ad_group.save(request)
            new_settings.save(request)

            actionlogs_to_send.extend(
                api.order_ad_group_settings_update(ad_group, current_settings, new_settings, request, send=False)
            )

        zwei_actions.send(actionlogs_to_send)

    def get_default_settings_dict(self, ad_group):
        settings = ad_group.campaign.get_current_settings()

        return {
            'target_devices': settings.target_devices,
            'target_regions': settings.target_regions
        }

    def get_retargetable_adgroups(self, request, ad_group_id):
        '''
        Get adgroups that can retarget this adgroup
        '''
        if not request.user.has_perm('zemauth.can_view_retargeting_settings'):
            return []

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        account = ad_group.campaign.account

        ad_groups = models.AdGroup.objects.filter(
            campaign__account=account
        ).select_related('campaign').order_by('id')

        ad_group_settings = models.AdGroupSettings.objects.all().filter(
            ad_group__campaign__account=account
        ).group_current_settings().values_list('ad_group__id', 'archived')
        archived_map = {adgs[0]: adgs[1] for adgs in ad_group_settings}

        return [
            {
                'id': adg.id,
                'name': adg.name,
                'archived': archived_map.get(adg.id) or False,
                'campaign_name': adg.campaign.name,
            }
            for adg in ad_groups
        ]


class AdGroupSettingsState(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_state_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_control_ad_group_state_in_table'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        current_settings = ad_group.get_current_settings()
        return self.create_api_response({
            'id': str(ad_group.pk),
            'state': current_settings.state,
        })

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_state_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_control_ad_group_state_in_table'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)
        data = json.loads(request.body)
        new_state = data.get('state')

        campaign_settings = ad_group.campaign.get_current_settings()
        self._validate_state(ad_group, ad_group.campaign, campaign_settings, new_state)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()

        if new_settings.state != new_state:
            new_settings.state = new_state
            new_settings.save(request)
            actionlog_api.init_set_ad_group_state(ad_group, new_settings.state, request, send=True)
            k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettingsState.post')

        return self.create_api_response({
            'id': str(ad_group.pk),
            'state': new_settings.state,
        })

    def _validate_state(self, ad_group, campaign, campaign_settings, state):
        if state is None or state not in constants.AdGroupSettingsState.get_all():
            raise exc.ValidationError()

        if not campaign_stop.can_enable_ad_group(ad_group, campaign, campaign_settings):
            raise exc.ValidationError('Please add additional budget to your campaign to make changes.')

        if state == constants.AdGroupSettingsState.ACTIVE:
            if not validation_helpers.ad_group_has_available_budget(ad_group):
                raise exc.ValidationError('Cannot enable ad group without available budget.')

            if models.CampaignGoal.objects.filter(campaign=campaign).count() == 0:
                raise exc.ValidationError('Please add a goal to your campaign before enabling this ad group.')


class CampaignAgency(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_agency_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_agency_view'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        campaign_settings = campaign.get_current_settings()

        response = {
            'settings': self.get_dict(campaign_settings, campaign),
            'campaign_managers': self.get_user_list(campaign_settings),
            'history': self.get_history(campaign),
            'can_archive': campaign.can_archive(),
            'can_restore': campaign.can_restore(),
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'campaign_agency_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_agency_view'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        resource = json.loads(request.body)

        form = forms.CampaignAgencyForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        old_settings = campaign.get_current_settings()
        new_settings = old_settings.copy_settings()
        self.set_settings(new_settings, campaign, form.cleaned_data)

        helpers.save_campaign_settings_and_propagate(campaign, new_settings, request)
        helpers.log_and_notify_campaign_settings_change(campaign, old_settings, new_settings, request,
                                                        constants.UserActionType.SET_CAMPAIGN_AGENCY_SETTINGS)

        response = {
            'settings': self.get_dict(new_settings, campaign),
            'history': self.get_history(campaign),
            'can_archive': campaign.can_archive(),
            'can_restore': campaign.can_restore(),
        }

        return self.create_api_response(response)

    def get_history(self, campaign):
        settings = models.CampaignSettings.objects.\
            filter(campaign=campaign).\
            order_by('created_dt')

        history = []

        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            changes_text = models.CampaignSettings.get_changes_text(old_settings, new_settings)

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings)

            if new_settings.created_by is None and new_settings.system_user is not None:
                changed_by = constants.SystemUserType.get_text(new_settings.system_user)
            elif new_settings.created_by is None and new_settings.system_user is None:
                changed_by = automation.settings.AUTOMATION_AI_NAME
            else:
                changed_by = new_settings.created_by.email

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': changed_by,
                'changes_text': changes_text,
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict()

        for field in models.CampaignSettings._settings_fields:
            settings_dict[field] = {
                'name': models.CampaignSettings.get_human_prop_name(field),
                'value': models.CampaignSettings.get_human_value(
                    field, getattr(new_settings, field, models.CampaignSettings.get_default_value(field)))
            }

            if old_settings is not None:
                settings_dict[field]['old_value'] = models.CampaignSettings.get_human_value(
                    field, getattr(old_settings, field, models.CampaignSettings.get_default_value(field)))

        return settings_dict

    def get_dict(self, settings, campaign):
        result = {}

        if settings:
            result = {
                'id': str(campaign.pk),
                'name': campaign.name,
                'campaign_manager':
                    str(settings.campaign_manager.id)
                    if settings.campaign_manager is not None else None,
                'iab_category': settings.iab_category,
            }

        return result

    def set_settings(self, settings, campaign, resource):
        settings.campaign = campaign
        settings.campaign_manager = resource['campaign_manager']
        settings.iab_category = resource['iab_category']

    def get_user_list(self, settings):
        users = ZemUser.objects.all()

        manager = settings.campaign_manager
        if manager is not None and manager not in users:
            users.append(manager)

        return [{'id': str(user.id),
                 'name': helpers.get_user_full_name_or_email(user)} for user in users]


class CampaignConversionGoals(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_conversion_goals_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        rows = []
        for conversion_goal in campaign.conversiongoal_set.select_related('pixel').order_by('created_dt').all():
            row = {
                'id': conversion_goal.id,
                'type': conversion_goal.type,
                'name': conversion_goal.name,
                'conversion_window': conversion_goal.conversion_window,
                'goal_id': conversion_goal.goal_id,
            }

            if conversion_goal.type == constants.ConversionGoalType.PIXEL:
                row['pixel'] = {
                    'id': conversion_goal.pixel.id,
                    'slug': conversion_goal.pixel.slug,
                    'url': conversions_helper.get_conversion_pixel_url(campaign.account_id, conversion_goal.pixel.slug),
                    'archived': conversion_goal.pixel.archived,
                }

            rows.append(row)

        available_pixels = []
        for conversion_pixel in campaign.account.conversionpixel_set.filter(archived=False):
            available_pixels.append({
                'id': conversion_pixel.id,
                'slug': conversion_pixel.slug,
            })

        return self.create_api_response({
            'rows': rows,
            'available_pixels': available_pixels
        })

    @statsd_helper.statsd_timer('dash.api', 'campaign_conversion_goals_post')
    def post(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError(message='Invalid json')

        form = forms.ConversionGoalForm(
            {
                'name': data.get('name'),
                'type': data.get('type'),
                'conversion_window': data.get('conversion_window'),
                'goal_id': data.get('goal_id'),
            },
            campaign_id=campaign_id
        )
        campaign_goals.create_conversion_goal(request, form, campaign)

        return self.create_api_response()


class ConversionGoal(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_conversion_goals_delete')
    def delete(self, request, campaign_id, conversion_goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)  # checks authorization
        campaign_goals.delete_conversion_goal(request, conversion_goal_id, campaign)

        return self.create_api_response()


class CampaignGoalValidation(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_goal_validate_put')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.can_see_campaign_goals'):
            raise exc.MissingDataError()
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_goal = json.loads(request.body)
        goal_form = forms.CampaignGoalForm(campaign_goal, campaign_id=campaign.pk)

        errors = {}
        if not goal_form.is_valid():
            errors.update(dict(goal_form.errors))

        if campaign_goal['type'] == constants.CampaignGoalKPI.CPA:
            if not campaign_goal.get('id'):
                conversion_form = forms.ConversionGoalForm(
                    campaign_goal.get('conversion_goal', {}),
                    campaign_id=campaign.pk,
                )
                if not conversion_form.is_valid():
                    errors['conversion_goal'] = conversion_form.errors

        if errors:
            raise exc.ValidationError(errors=errors)

        return self.create_api_response()


class CampaignSettings(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        response = {
            'settings': self.get_dict(request, campaign_settings, campaign),
        }

        if request.user.has_perm('zemauth.can_see_campaign_goals'):
            response['goals'] = self.get_campaign_goals(
                campaign
            )

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_put')
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

        if len(current) - len(changes['removed']) + len(changes['added']) <= 0:
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
            helpers.save_campaign_settings_and_propagate(campaign, new_settings, request)
            helpers.log_and_notify_campaign_settings_change(
                campaign, current_settings, new_settings, request,
                constants.UserActionType.SET_CAMPAIGN_SETTINGS
            )

        response = {
            'settings': self.get_dict(request, new_settings, campaign)
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

            if goal['conversion_goal']:
                conversion_form = forms.ConversionGoalForm(
                    {
                        'name': goal['conversion_goal'].get('name'),
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
                goal_blob['conversion_goal']['pixel_url'] =\
                    conversions_helper.get_conversion_pixel_url(
                        campaign.account.id,
                        conversion_goal.pixel.slug
                    )
            ret.append(goal_blob)
        return ret

    def get_dict(self, request, settings, campaign):
        if not settings:
            return {}

        result = {
            'id': str(campaign.pk),
            'name': campaign.name,
            'campaign_goal': settings.campaign_goal,
            'goal_quantity': settings.goal_quantity,
        }

        result['target_devices'] = settings.target_devices
        result['target_regions'] = settings.target_regions

        return result

    def set_settings(self, request, settings, campaign, resource):
        settings.name = resource['name']
        settings.campaign_goal = resource['campaign_goal']
        settings.goal_quantity = resource['goal_quantity']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']

    def set_campaign(self, campaign, resource):
        campaign.name = resource['name']


class AccountConversionPixels(api_common.BaseApiView):

    def _get_pixel_status(self, last_verified_dt):
        if last_verified_dt is None:
            return constants.ConversionPixelStatus.NOT_USED

        if last_verified_dt > datetime.datetime.utcnow() - datetime.timedelta(days=CONVERSION_PIXEL_INACTIVE_DAYS):
            return constants.ConversionPixelStatus.ACTIVE

        return constants.ConversionPixelStatus.INACTIVE

    @statsd_helper.statsd_timer('dash.api', 'conversion_pixels_list')
    def get(self, request, account_id):
        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)
        last_verified_dts = redshift.get_pixels_last_verified_dt(account_id=account_id)

        rows = [
            {
                'id': conversion_pixel.id,
                'slug': conversion_pixel.slug,
                'url': conversions_helper.get_conversion_pixel_url(account.id, conversion_pixel.slug),
                'status': constants.ConversionPixelStatus.get_text(
                    self._get_pixel_status(last_verified_dts.get((account_id, conversion_pixel.slug)))),
                'last_verified_dt': last_verified_dts.get((account_id, conversion_pixel.slug)),
                'archived': conversion_pixel.archived
            } for conversion_pixel in models.ConversionPixel.objects.filter(account=account)
        ]

        return self.create_api_response({
            'rows': rows,
            'conversion_pixel_tag_prefix': settings.CONVERSION_PIXEL_PREFIX + str(account.id) + '/',
        })

    @statsd_helper.statsd_timer('dash.api', 'conversion_pixel_post')
    def post(self, request, account_id):
        account = helpers.get_account(request.user, account_id)  # check access to account

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        slug = data.get('slug')

        form = forms.ConversionPixelForm({'slug': slug})
        if not form.is_valid():
            raise exc.ValidationError(message=' '.join(dict(form.errors)['slug']))

        try:
            models.ConversionPixel.objects.get(account_id=account_id, slug=slug)
            raise exc.ValidationError(message='Conversion pixel with this identifier already exists.')
        except models.ConversionPixel.DoesNotExist:
            pass

        with transaction.atomic():
            conversion_pixel = models.ConversionPixel.objects.create(account_id=account_id, slug=slug)

            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Added conversion pixel with unique identifier {}.'.format(slug)
            new_settings.save(request)

        email_helper.send_account_pixel_notification(account, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_CONVERSION_PIXEL, account=account)

        return self.create_api_response({
            'id': conversion_pixel.id,
            'slug': conversion_pixel.slug,
            'url': conversions_helper.get_conversion_pixel_url(account.id, slug),
            'status': constants.ConversionPixelStatus.get_text(
                constants.ConversionPixelStatus.NOT_USED),
            'last_verified_dt': None,
            'archived': conversion_pixel.archived,
        })


class ConversionPixel(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'conversion_pixel_put')
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

        if 'archived' in data:
            if not request.user.has_perm('zemauth.archive_restore_entity'):
                raise exc.AuthorizationError()

            if not isinstance(data['archived'], bool):
                raise exc.ValidationError(message='Invalid value')

            with transaction.atomic():
                conversion_pixel.archived = data['archived']
                conversion_pixel.save()

                new_settings = account.get_current_settings().copy_settings()
                new_settings.changes_text = u'{} conversion pixel with unique identifier {}.'.format(
                    'Archived' if data['archived'] else 'Restored',
                    conversion_pixel.slug
                )
                new_settings.save(request)

            helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_CONVERSION_PIXEL,
                                                account=account)

        return self.create_api_response({
            'id': conversion_pixel.id,
            'archived': conversion_pixel.archived,
        })


class AccountHistory(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_history_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_history_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        response = {
            'history': self.get_history(account),
        }
        return self.create_api_response(response)

    def get_history(self, account):
        settings = models.AccountSettings.objects.\
            filter(account=account).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            settings_dict = self.convert_settings_to_dict(new_settings, old_settings)
            changes_text = self.get_changes_text(new_settings, old_settings)

            if not changes_text:
                continue

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': changes_text,
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def convert_settings_to_dict(self, new_settings, old_settings):
        settings_dict = OrderedDict([
            ('name', {
                'name': 'Name',
                'value': new_settings.name.encode('utf-8')
            }),
            ('archived', {
                'name': 'Archived',
                'value': str(new_settings.archived)
            }),
            ('default_account_manager', {
                'name': 'Account Manager',
                'value': helpers.get_user_full_name_or_email(new_settings.default_account_manager)
            }),
            ('default_sales_representative', {
                'name': 'Sales Representative',
                'value': helpers.get_user_full_name_or_email(new_settings.default_sales_representative)
            }),
            ('account_type', {
                'name': 'Account Type',
                'value': constants.AccountType.get_text(new_settings.account_type)
            }),
        ])

        if old_settings is not None:
            settings_dict['name']['old_value'] = old_settings.name.encode('utf-8')
            settings_dict['archived']['old_value'] = str(old_settings.archived)

            if old_settings.default_account_manager is not None:
                settings_dict['default_account_manager']['old_value'] = \
                    helpers.get_user_full_name_or_email(old_settings.default_account_manager)

            if old_settings.default_sales_representative is not None:
                settings_dict['default_sales_representative']['old_value'] = \
                    helpers.get_user_full_name_or_email(old_settings.default_sales_representative)

            if old_settings.account_type is not None:
                settings_dict['account_type']['old_value'] = constants.AccountType.get_text(old_settings.account_type)

        return settings_dict

    def get_changes_text(self, new_settings, old_settings):
        if not old_settings:
            return 'Created settings'

        changes_text = ', '.join(filter(None, [
            self.get_changes_text_for_settings(new_settings, old_settings),
            new_settings.changes_text.encode('utf-8') if new_settings.changes_text is not None else ''
        ]))

        return changes_text

    def get_changes_text_for_settings(self, new_settings, old_settings):
        change_strings = []
        changes = old_settings.get_setting_changes(new_settings)
        settings_dict = self.convert_settings_to_dict(new_settings, None)

        for key in changes:
            setting = settings_dict[key]
            change_strings.append(
                '{} set to "{}"'.format(setting['name'], setting['value'])
            )

        return ', '.join(change_strings)


class AccountSettings(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_agency_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        user_agency = None
        if helpers.is_agency_manager(request.user, account):
            user_agency = helpers.get_user_agency(request.user)

        response = {
            'settings': self.get_dict(request, account_settings, account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
        }

        if request.user.has_perm('zemauth.can_modify_account_manager'):
            response['account_managers'] = self.get_user_list(account_settings, agency=user_agency)

        if request.user.has_perm('zemauth.can_set_account_sales_representative'):
            response['sales_reps'] = self.get_user_list(account_settings, 'campaign_settings_sales_rep')
        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'account_agency_put')
    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.AccountSettingsForm(resource.get('settings', {}))

        settings = self.save_settings(request, account, form)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.SET_ACCOUNT_AGENCY_SETTINGS,
                                            account=account)
        response = {
            'settings': self.get_dict(request, settings, account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
        }

        return self.create_api_response(response)

    def save_settings(self, request, account, form):
        with transaction.atomic():
            # Form is additionally validated in self.set_allowed_sources method
            if not form.is_valid():
                data = self.get_validation_error_data(request, account)
                raise exc.ValidationError(errors=dict(form.errors), data=data)

            self._validate_essential_account_settings(request.user, form)

            self.set_account(account, form.cleaned_data)

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

            if 'allowed_sources' in form.cleaned_data and\
                    form.cleaned_data['allowed_sources'] is not None:
                self.set_allowed_sources(
                    settings,
                    account,
                    request.user.has_perm('zemauth.can_see_all_available_sources'),
                    form
                )

            account.save(request)
            settings.save(request)
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

    def set_account(self, account, resource):
        if resource['name']:
            account.name = resource['name']

    def get_non_removable_sources(self, account, sources_to_be_removed):
        non_removable_source_ids_list = []

        for campaign in models.Campaign.objects.filter(account_id=account.id).exclude_archived():

            for adgroup in campaign.adgroup_set.filter(is_demo=False):
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

        if to_be_added or to_be_removed:
            settings.changes_text = self.get_changes_text_for_media_sources(to_be_added, to_be_removed)
            account.allowed_sources.add(*list(to_be_added))
            account.allowed_sources.remove(*list(to_be_removed))

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

    def get_user_list(self, settings, perm_name=None, agency=None):
        users = ZemUser.objects.get_users_with_perm(perm_name) if perm_name else ZemUser.objects.all()

        if agency is not None:
            users = users.filter(pk=agency.users.all()) | \
                users.filter(account__agency=agency)

        users = list(users.filter(is_active=True).distinct())

        manager = settings.default_account_manager
        if manager is not None and manager not in users:
            users.append(manager)

        return [{'id': str(user.id), 'name': helpers.get_user_full_name_or_email(user)} for user in users]


class AdGroupAgency(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_agency_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        response = {
            'history': self.get_history(ad_group, request.user),
            'can_archive': ad_group.can_archive(),
            'can_restore': ad_group.can_restore(),
        }

        return self.create_api_response(response)

    @newrelic.agent.function_trace()
    def get_history(self, ad_group, user):
        ad_group_settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('created_dt').\
            select_related('created_by')

        history = []
        for i in range(0, len(ad_group_settings)):
            old_settings = ad_group_settings[i - 1] if i > 0 else None
            new_settings = ad_group_settings[i]

            changes_text = models.AdGroupSettings.get_changes_text(old_settings, new_settings, user)

            if i > 0 and not len(changes_text):
                continue

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings, user)
            if new_settings.created_by is None:
                changed_by = automation.settings.AUTOMATION_AI_NAME
                if new_settings.system_user:
                    changed_by = constants.SystemUserType.get_text(new_settings.system_user)
            else:
                changed_by = new_settings.created_by.email
            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': changed_by,
                'changes_text': changes_text,
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    @newrelic.agent.function_trace()
    def convert_settings_to_dict(self, old_settings, new_settings, user):
        settings_dict = OrderedDict()
        for field in models.AdGroupSettings._settings_fields:
            if field in ['enable_adobe_tracking', 'adobe_tracking_param'] and\
                    not user.has_perm('zemauth.can_toggle_adobe_performance_tracking'):
                continue

            settings_dict[field] = {
                'name': models.AdGroupSettings.get_human_prop_name(field),
                'value': models.AdGroupSettings.get_human_value(field, getattr(
                    new_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
            }

            if old_settings is not None:
                old_value = models.AdGroupSettings.get_human_value(field, getattr(
                    old_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
                settings_dict[field]['old_value'] = old_value

        return settings_dict


class AccountUsers(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_access_users_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        agency_users = account.agency.users.all() if account.agency else []

        users = [self._get_user_dict(u) for u in account.users.all()]
        agency_managers = [self._get_user_dict(u) for u in agency_users]

        return self.create_api_response({
            'users': users,
            'agency_managers': agency_managers if account.agency else None,
        })

    @statsd_helper.statsd_timer('dash.api', 'account_access_users_put')
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

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Added user {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

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

    @statsd_helper.statsd_timer('dash.api', 'account_access_users_delete')
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

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Removed user {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

        return self.create_api_response({
            'user_id': user.id
        })

    def _get_user_dict(self, user):
        return {
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'last_login': user.last_login.date(),
            'is_active': user.last_login != user.date_joined,
        }


class UserActivation(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_user_activation_mail_post')
    def post(self, request, account_id, user_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.AuthorizationError()

        try:
            user = ZemUser.objects.get(pk=user_id)
            email_helper.send_email_to_new_user(user, request)

            account = helpers.get_account(request.user, account_id)
            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Resent activation mail {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

        except ZemUser.DoesNotExist:
            raise exc.ValidationError(
                pretty_message=u'Cannot activate nonexisting user.'
            )

        return self.create_api_response({})


class CampaignContentInsights(api_common.BaseApiView):

    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.can_view_campaign_content_insights_side_tab'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        best_performer_rows, worst_performer_rows = self._fetch_content_ad_metrics(
            request.user,
            campaign,
            start_date,
            end_date,
            limit=8
        )

        return self.create_api_response({
            'summary': 'Title',
            'metric': 'CTR',
            'best_performer_rows': best_performer_rows,
            'worst_performer_rows': worst_performer_rows,
        })

    def _fetch_content_ad_metrics(self, user, campaign, start_date, end_date, limit=8):
        stats = stats_helper.get_content_ad_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=['content_ad'],
            ignore_diff_rows=True,
            constraints={'campaign': campaign.id}
        )
        mapped_stats = {stat['content_ad']: stat for stat in stats}
        dd_ads = self._deduplicate_content_ad_titles(campaign)

        dd_cad_metric = []
        for title, caids in dd_ads.iteritems():
            clicks = sum(map(lambda caid: mapped_stats.get(caid, {}).get('clicks', 0) or 0, caids))
            impressions = sum(map(lambda caid: mapped_stats.get(caid, {}).get('impressions', 0) or 0, caids))
            metric = float(clicks) / impressions if impressions > 0 else None
            dd_cad_metric.append({
                'summary': title,
                'metric': '{:.2f}%'.format(metric*100) if metric else None,
                'value': metric or 0,
                'clicks': clicks or 0,
            })

        top_cads = sorted(dd_cad_metric, key=lambda dd_cad: dd_cad['value'], reverse=True)[:limit]

        active_dd_cad_metric = [cad_metric for cad_metric in dd_cad_metric if cad_metric['clicks'] >= 10]
        bott_cads = sorted(active_dd_cad_metric, key=lambda dd_cad: dd_cad['value'])[:limit]
        return [{'summary': cad['summary'], 'metric': cad['metric']} for cad in top_cads],\
            [{'summary': cad['summary'], 'metric': cad['metric']} for cad in bott_cads]

    def _deduplicate_content_ad_titles(self, campaign):
        ads = models.ContentAd.objects.all().filter(
            ad_group__campaign=campaign
        ).exclude_archived().values_list('id', 'title')
        ret = defaultdict(list)
        for caid, title in ads:
            ret[title].append(caid)
        return ret
