import json

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.conf import settings

from utils import api_common
import dash.models
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
        account_items = filter_choices(
            (account.id, str(account)) for account in dash.models.Account.objects.all()
        )
        campaign_items = filter_choices(
            (campaign.id, str(campaign)) for campaign in dash.models.Campaign.objects.all()
        )
        network_items = filter_choices(
            (network.id, str(network)) for network in dash.models.Network.objects.all()
        )

        return {
            'state': state_items,
            'network': network_items,
            'campaign': campaign_items,
            'account': account_items,
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
        if filters.get('campaign'):
            actions = actions.filter(ad_group_network__ad_group__campaign=filters['campaign'])
        if filters.get('account'):
            actions = actions.filter(ad_group_network__ad_group__campaign__account=filters['account'])

        return [self._get_action_item(action) for action in actions]

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
                str(action.ad_group_network.ad_group),
                action.ad_group_network.ad_group.id,
            ],
            'network': [
                str(action.ad_group_network.network),
                action.ad_group_network.network.id,
            ],
            'campaign': [
                str(action.ad_group_network.ad_group.campaign),
                action.ad_group_network.ad_group.campaign.id
            ],
            'account': [
                str(action.ad_group_network.ad_group.campaign.account),
                action.ad_group_network.ad_group.campaign.account.id
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

        action = models.ActionLog.objects.get(id=action_log_id)
        action.state = resource['state']
        action.save()

        response = {}
        response['actionLogItem'] = self._get_action_item(action)

        print response

        return self.create_api_response(response)
