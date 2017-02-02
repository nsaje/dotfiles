import json

from dash import forms
from dash import publisher_group_helpers

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
        if not publisher_group_helpers.can_user_handle_publishers(request.user, obj):
            raise exc.AuthorizationError()

        # TODO: accepts empty collection but does nothing with it - compatibility with old
        # publishers blacklisting endpoint
        entry_dicts = form.cleaned_data['entries']
        if entry_dicts:
            publisher_group_helpers.handle_publishers(
                request, entry_dicts, obj,
                form.cleaned_data['status'])

        response = {"success": True}
        return self.create_api_response(response)
