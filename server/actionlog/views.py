import json

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.conf import settings
from django.core import urlresolvers

from utils import api_common
from utils import exc
from utils import statsd_helper
import dash.models
import dash.constants

from actionlog import models
from actionlog import constants


ACTION_LOG_DISPLAY_MAX_ACTION = 100
ACTION_LOG_STATE_OPTIONS = {-1, 1, 2}


@permission_required('actionlog.manual_view')
def action_log(request):
    return render(request, 'action_log.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class ActionLogApiView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('actionlog.api', 'view_get')
    @method_decorator(permission_required('actionlog.manual_view'))
    def get(self, request):
        response = {}

        actions = self._get_actions(request)

        response['actionLogItems'] = self._prepare_actions(actions)
        response['actionLogItemsMax'] = ACTION_LOG_DISPLAY_MAX_ACTION
        response['filters'] = self._get_filters(request, actions)

        return self.create_api_response(response)

    def _get_filters(self, request, actions):
        unfiltered = (0, 'All')
        filter_choices = lambda x: [unfiltered] + list(x)

        state_items = filter_choices(
            choice for choice in constants.ActionState.get_choices() if choice[0] in ACTION_LOG_STATE_OPTIONS
        )

        ad_groups = dash.models.AdGroup.objects.filter(adgroupsource__actionlog__in=actions).distinct().select_related('campaign__account')
        ad_group_items = filter_choices(
            (ad_group.id, self._get_ad_group_full_name(ad_group)) for ad_group in ad_groups
        )

        sources = dash.models.Source.objects.filter(adgroupsource__actionlog__in=actions).distinct()
        source_items = filter_choices(
            (source.id, str(source)) for source in sources
        )

        return {
            'state': state_items,
            'source': source_items,
            'ad_group': ad_group_items,
        }

    def _get_take_action(self, action):
        NAMES = {
            'start_date': 'Start date',
            'end_date': 'End date',
            'cpc_cc': 'Max CPC bid',
            'daily_budget_cc': 'Daily budget',
            'target_devices': 'Device targeting',
            'target_regions': 'Locations',
            'tracking_code': 'Tracking code',
            'state': 'State'
        }

        if action.action == constants.Action.SET_PROPERTY:
            prop = action.payload.get('property')
            val = action.payload.get('value')

            if prop == 'state':
                val = dash.constants.AdGroupSourceSettingsState.get_text(val)
            elif prop == 'end_date' and val is None:
                val = '"I\'ll stop it myself"'
            elif prop == 'target_regions' and not val:
                val = '"worldwide"'
            else:
                val = json.dumps(val)

            return '{} set to {}'.format(NAMES.get(prop) or prop, val)
        elif action.action == constants.Action.SET_CAMPAIGN_STATE:
            state = action.payload.get('args', {}).get('conf', {}).get('state')

            if state not in dash.constants.AdGroupSourceSettingsState.get_all():
                 raise Exception('Unsupported state %s for action SET_CAMPAIGN_STATE' % state)

            return '{} set to {}'.format(NAMES.get('state'), dash.constants.AdGroupSourceSettingsState.get_text(state))
        else:
            raise Exception('Unsupported action %s' % action.action)

    def _get_actions(self, request):
        actions = models.ActionLog.objects.filter(
            action_type=constants.ActionType.MANUAL,
        )

        try:
            filters = json.loads(request.GET.get('filters', ''))
        except ValueError:
            filters = {}

        if filters.get('state') in ACTION_LOG_STATE_OPTIONS:
            actions = actions.filter(state=filters['state'])
        else:
            actions = actions.filter(state__in=ACTION_LOG_STATE_OPTIONS)

        if filters.get('source'):
            actions = actions.filter(ad_group_source__source=filters['source'])
        if filters.get('ad_group'):
            actions = actions.filter(ad_group_source__ad_group=filters['ad_group'])

        return actions.select_related(
            'modified_by',
            'created_by',
            'ad_group_source__ad_group__campaign__account',
            'order',
            'ad_group_source__source'
        )

    def _prepare_actions(self, actions):
        actions = actions[:ACTION_LOG_DISPLAY_MAX_ACTION]

        return [self._get_action_item(action) for action in actions]

    def _get_ad_group_full_name(self, ad_group):
        return '{account} / {campaign} / {ad_group}'.format(
            account=ad_group.campaign.account,
            campaign=ad_group.campaign,
            ad_group=ad_group,
        )

    def _get_action_item(self, action):
        return {
            'id': action.id,

            'action': action.action,
            'state': [
                constants.ActionState.get_text(action.state),
                action.state
            ],

            'ad_group_source': [
                str(action.ad_group_source),
                action.ad_group_source.id,
            ],

            'ad_group': [
                self._get_ad_group_full_name(action.ad_group_source.ad_group),
                action.ad_group_source.ad_group.id,
            ],
            'source': [
                str(action.ad_group_source.source),
                action.ad_group_source.source.id,
            ],

            'created_dt': action.created_dt,
            'modified_dt': action.modified_dt,

            'created_by': [action.created_by.email, action.created_by.id] if action.created_by else ['Automatically created', None],
            'modified_by': action.modified_by and [action.modified_by.email, action.modified_by.id],

            'order': action.order and action.order.id,

            'take_action': self._get_take_action(action),
            'supply_dash_url': urlresolvers.reverse('dash.views.views.supply_dash_redirect') \
                + '?ad_group_id={}&source_id={}'.format(action.ad_group_source.ad_group.id, action.ad_group_source.source.id)
        }

    @statsd_helper.statsd_timer('actionlog.api', 'view_put')
    @method_decorator(permission_required('actionlog.manual_acknowledge'))
    def put(self, request, action_log_id):

        resource = json.loads(request.body)

        new_state = resource.get('state')
        if new_state not in ACTION_LOG_STATE_OPTIONS:
            raise exc.ValidationError('Invalid state')

        action = models.ActionLog.objects.get(id=action_log_id)
        action.state = new_state
        action.save()

        response = {}
        response['actionLogItem'] = self._get_action_item(action)

        return self.create_api_response(response)
