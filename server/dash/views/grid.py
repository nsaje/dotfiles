"""
Settings API Workaround - use old API to save settings and return updates

TODO when we move base level:
  - converters should not be needed anymore and should be deleted
  - with that it becomes a pure view module for saving data, rename acording to that
"""

import datetime
import json

from dash import views
from dash import constants
from dash import table
from dash.views import helpers

import stats.helpers

from utils import api_common
from utils import exc


class AdGroupSettings (api_common.BaseApiView):
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.MissingDataError()
        data = json.loads(request.body)
        settings = data['settings']
        state = settings.get('state')
        if not state:
            # Only state supported atm.
            raise exc.ValidationError()

        request._body = json.dumps(settings)
        views.agency.AdGroupSettingsState().post(request, ad_group_id)

        response = {'rows': [{'ad_group': ad_group_id, 'state': state}]}
        convert_resource_response(constants.Level.CAMPAIGNS, 'ad_group_id', response)
        return self.create_api_response(response)


class ContentAdSettings(api_common.BaseApiView):
    def post(self, request, content_ad_id):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.MissingDataError()
        data = json.loads(request.body)
        settings = data['settings']
        content_ad = views.helpers.get_content_ad(request.user, content_ad_id, select_related=True)
        ad_group = content_ad.ad_group
        state = settings.get('state')
        if not state:
            # Only state supported atm.
            raise exc.ValidationError()

        request_settings = {
            'state': state,
            'content_ad_ids_selected': [content_ad_id]
        }
        request._body = json.dumps(request_settings)
        views.views.AdGroupContentAdState().post(request, ad_group.id)

        response = {'rows': [{'id': content_ad_id, 'status_setting': state}]}
        convert_resource_response(constants.Level.AD_GROUPS, 'content_ad_id', response)
        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):
    def post(self, request, ad_group_id, source_id):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.MissingDataError()
        data = json.loads(request.body)
        config = data['config'] if 'config' in data else {}
        settings = data['settings']
        # Save current timestamp to retrieve updates caused by save
        last_change_dt = datetime.datetime.now()
        filtered_sources = []
        if 'filtered_sources' in config:
            filtered_sources = config['filtered_sources']

        request._body = json.dumps(settings)
        response_save_http = views.views.AdGroupSourceSettings().put(request, ad_group_id, source_id)
        response_save = json.loads(response_save_http.content)['data']
        response_update = table.AdGroupSourcesTableUpdates()\
            .get(request.user, last_change_dt, filtered_sources, ad_group_id_=ad_group_id)

        response = {}
        response.update(response_save)
        response.update(response_update)
        convert_update_response(response, source_id)
        convert_resource_response(constants.Level.AD_GROUPS, 'source_id', response)

        if 'autopilot_changed_sources' in response and response['autopilot_changed_sources']:
            response['notification'] = self.create_changed_sources_notification(response['autopilot_changed_sources'])

        return self.create_api_response(response)

    def create_changed_sources_notification(self, sources):
        return {
            'type': 'info',
            'msg': 'Following your change to a Media Source\'s state, Autopilot has ' +
                   'successfully adjusted daily budgets of the following Media Sources: {}.'
                   .format(sources)
        }


def convert_update_response(response, updated_id):
    if 'rows' in response:
        rows = []
        for id, row in response['rows'].iteritems():
            row['id'] = str(id)
            if row['id'] == updated_id:
                row['editable_fields'] = response['editable_fields']
            rows.append(row)
        response['rows'] = rows
        del response['editable_fields']


def convert_resource_response(level, base_dimension, response):
    if 'rows' in response:
        _convert_breakdown_fields(base_dimension, response)
        _convert_status_field(level, base_dimension, response)
        _convert_status_setting_field(level, base_dimension, response)
    return response


def _convert_breakdown_fields(base_dimension, response):
    # Keys varies in some level/breakdown variations
    id_key = {
        'campaign_id': 'campaign',
        'ad_group_id': 'ad_group',
    }.get(base_dimension, 'id')

    name_key = 'title' if base_dimension == 'content_ad_id' else 'name'
    breakdown_id_fields = [id_key]

    if base_dimension == 'publisher_id':
        id_key = 'domain'
        name_key = 'domain'
        breakdown_id_fields = ['domain', 'source_id']

    for row in response['rows']:
        if id_key in row:
            row['id'] = row[id_key]
            row['breakdown_id'] = stats.helpers.encode_breakdown_id(breakdown_id_fields, row)
            row['parent_breakdown_id'] = None
        if name_key in row:
            row['breakdown_name'] = row[name_key]


def _convert_status_field(level, base_dimension, response):
    # TODO this shouldn't be necessary when we migrate base level to stats
    for row in response['rows']:
        if base_dimension == 'account_id' and 'status' in row:
            row['status'] = {'value': row['status']}

        if base_dimension == 'campaign_id' and 'state' in row:
            row['status'] = {'value': row['state']}
            del row['state']

        if base_dimension == 'ad_group_id' and 'state' in row:
            row['status'] = {'value': row['state']}
            row['state'] = {'value': row['state']}

        if base_dimension == 'content_ad_id' and 'status_setting' in row:
            row['status'] = {'value': row['status_setting']}

        if base_dimension == 'source_id' and \
                level in [constants.Level.ALL_ACCOUNTS, constants.Level.ACCOUNTS, constants.Level.CAMPAIGNS] \
                and 'status' in row:
            row['status'] = {'value': row['status']}

        if base_dimension == 'source_id' and level == constants.Level.AD_GROUPS:
            status = {'value': row['status']}
            if 'notifications' in response:
                # Notifications are only set for rows for enabled sources in paused ad groups. This is a workaround to
                # append notification message to status dict and changing status value to inactive (sources can not have
                # enabled status in paused ad groups).
                for notification_row_id in response['notifications']:
                    if int(row['id']) == notification_row_id:
                        status['value'] = constants.AdGroupSourceSettingsState.INACTIVE
                        status['popover_message'] = response['notifications'][notification_row_id]['message']
                        status['important'] = True
            row['status'] = status

        if base_dimension == 'publisher_id':
            status = {'value': row['status']}
            if 'blacklisted_level_description' in row:
                status['popover_message'] = row['blacklisted_level_description']
            row['status'] = status


def _convert_status_setting_field(level, base_dimension, response):
    if level != constants.Level.AD_GROUPS or base_dimension not in ['content_ad_id', 'source_id']:
        return

    for row in response['rows']:
        if 'status_setting' in row:
            row['state'] = {'value': row['status_setting']}
            del row['status_setting']
            if 'editable_fields' in row and 'status_setting' in row['editable_fields']:
                row['editable_fields']['state'] = row['editable_fields']['status_setting']
                del row['editable_fields']['status_setting']
