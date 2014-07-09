import json

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.conf import settings

from utils import api_common
from utils import exc
import dash.models
import dash.constants

from actionlog import models
from actionlog import constants


ACTION_LOG_DISPLAY_MAX_ACTION = 1000
ACTION_LOG_STATE_OPTIONS = {-1, 1, 2}


@permission_required('actionlog.manual_view')
def action_log(request):
    return render(request, 'action_log.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class ActionLogApiView(api_common.BaseApiView):

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

        ad_groups = dash.models.AdGroup.objects.filter(adgroupnetwork__actionlog__in=actions).distinct()
        ad_group_items = filter_choices(
            (ad_group.id, self._get_ad_group_full_name(ad_group)) for ad_group in ad_groups
        )

        networks = dash.models.Network.objects.filter(adgroupnetwork__actionlog__in=actions).distinct()
        network_items = filter_choices(
            (network.id, str(network)) for network in networks
        )

        return {
            'state': state_items,
            'network': network_items,
            'ad_group': ad_group_items,
        }

    def _get_take_action(self, action):
        if action.action == constants.Action.SET_PROPERTY:
            prop = action.payload.get('property')
            val = action.payload.get('value')

            if prop == 'state':
                val = dash.constants.AdGroupNetworkSettingsState.get_text(val)
            else:
                val = json.dumps(val)

            return '{} to {}'.format(prop, val)
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

        if filters.get('state'):
            actions = actions.filter(state=filters['state'])
        if filters.get('network'):
            actions = actions.filter(ad_group_network__network=filters['network'])
        if filters.get('ad_group'):
            actions = actions.filter(ad_group_network__ad_group=filters['ad_group'])

        return actions

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

            'ad_group_network': [
                str(action.ad_group_network),
                action.ad_group_network.id,
            ],

            'ad_group': [
                self._get_ad_group_full_name(action.ad_group_network.ad_group),
                action.ad_group_network.ad_group.id,
            ],
            'network': [
                str(action.ad_group_network.network),
                action.ad_group_network.network.id,
            ],

            'created_dt': action.created_dt,
            'modified_dt': action.modified_dt,

            'created_by': action.created_by and [action.created_by.email, action.created_by.id],
            'modified_by': action.modified_by and [action.modified_by.email, action.modified_by.id],

            'order': action.order and action.order.id,

            'take_action': self._get_take_action(action),
        }

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
