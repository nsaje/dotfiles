import json

from dash import constants
from dash import forms
from dash import publisher_group_helpers
from dash import models
from dash import cpc_constraints

import redshiftapi.api_breakdowns

from utils import api_common
from utils import exc


class PublisherTargeting(api_common.BaseApiView):

    def post(self, request):
        if not request.user.has_perm('zemauth.can_modify_publisher_blacklist_status'):
            raise exc.MissingDataError()
        resource = json.loads(request.body)
        form = forms.PublisherTargetingForm(request.user, resource)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        obj = form.get_publisher_group_level_obj()
        if not publisher_group_helpers.can_user_handle_publisher_listing_level(request.user, obj):
            raise exc.AuthorizationError()

        entry_dicts = form.cleaned_data['entries']

        if form.cleaned_data['select_all']:
            entry_dicts = self.get_bulk_selection(form.cleaned_data)

        if entry_dicts:
            try:
                publisher_group_helpers.handle_publishers(
                    request, entry_dicts, obj,
                    form.cleaned_data['status'],
                    enforce_cpc=form.cleaned_data['enforce_cpc'])
            except cpc_constraints.CpcValidationError as e:
                raise exc.ValidationError(errors={
                    'cpc_constraints': list(e)
                })

        response = {"success": True}
        return self.create_api_response(response)

    def get_bulk_selection(self, obj, cleaned_data):

        constraints = {
            'date__gte': cleaned_data['start_date'],
            'date__lte': cleaned_data['end_date'],
            'source_id': list(cleaned_data['filtered_sources'].values_list('pk', flat=True).order_by('pk')),
        }

        if isinstance(obj, models.AdGroup):
            constraints['ad_group_id'] = obj.pk
        elif isinstance(obj, models.Campaign):
            constraints['campaign_id'] = obj.pk
        elif isinstance(obj, models.Account):
            constraints['account_id'] = obj.pk
        else:
            raise Exception('You probably don\'t want to blacklist all publishers globaly')

        entries_not_selected = cleaned_data["entries_not_selected"]
        if entries_not_selected:
            constraints['publisher_id__neq'] = [
                publisher_group_helpers.create_publisher_id(x['publisher'], x['source'].pk if x.get('source') else None)
                for x in entries_not_selected]

        publishers = redshiftapi.api_breakdowns.query_structure_with_stats(
            ['publisher_id'], constraints, use_publishers_view=True)

        sources = {x.pk: x for x in models.Source.objects.all()}
        entry_dicts = []
        for publisher_id in publishers:
            publisher, source_id = publisher_group_helpers.dissect_publisher_id(publisher_id)
            entry_dicts.append({
                'publisher': publisher,
                'source': sources[source_id] if source_id else None,
                'include_subdomains': cleaned_data['status'] == constants.PublisherTargetingStatus.BLACKLISTED,
            })
        return entry_dicts
