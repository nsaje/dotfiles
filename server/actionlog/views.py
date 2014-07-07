import json

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.conf import settings

from utils import api_common
import dash.constants

from actionlog import models
from actionlog import constants


@permission_required('actionlog.manual_view')
def action_log(request):
    return render(request, 'action_log.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class ActionLogApiView(api_common.BaseApiView):

    @method_decorator(permission_required('actionlog.manual_view'))
    def get(self, request):
        response = {}

        response['actionLogItems'] = self._get_actions(request)
        response['filters'] = self._get_filters(request)

        return self.create_api_response(response)

    def _get_filters(self, request):
        unfiltered = (0, 'All')

        filter_choices = lambda x: [unfiltered] + list(x)

        state_items = filter_choices(constants.ActionState.get_choices())

        return {
            'state': state_items,
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

        return [
            {
                'action': action.action,
                'state': [constants.ActionState.get_text(action.state), action.state],

                'ad_group_network': [str(action.ad_group_network), action.ad_group_network.id],

                'created_dt': action.created_dt,
                'modified_dt': action.modified_dt,

                'created_by': action.created_by and [action.created_by.email, action.created_by.id],
                'modified_by': action.modified_by and [action.modified_by.email, action.modified_by.id],

                'order': action.order and action.order.id,

                'take_action': self._get_take_action(action),
            } for action in actions
        ]

    @method_decorator(permission_required('actionlog.manual_acknowledge'))
    def put(self, request):
        return
