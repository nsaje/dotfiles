import json

from django.db import transaction

from dash import constants
from dash import forms
from dash import models
from utils import api_common
from utils import exc
import helpers


class AudiencesView(api_common.BaseApiView):
    def get(self, request, account_id, audience_id=None):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        if audience_id:
            return self._get_audience(request, account, audience_id)

        return self._get_audiences(request, account)

    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        resource = json.loads(request.body)
        audience_form = forms.AudienceForm(account, request.user, resource)
        if not audience_form.is_valid():
            raise exc.ValidationError(errors=dict(audience_form.errors))

        data = audience_form.cleaned_data

        audience_id = None
        with transaction.atomic():
            audience = models.Audience(
                name=data['name'],
                pixel_id=data['pixel_id'],
                ttl=data['ttl'],
            )
            audience.save(
                request,
                constants.HistoryActionType.AUDIENCE_CREATE,
                'Created audience "{}".'.format(audience.name)
            )
            audience_id = audience.pk

            for rule in audience_form.cleaned_data['rules']:
                rule = models.Rule(
                    audience=audience,
                    type=rule['type'],
                    value=rule['value'],
                )
                rule.save()

        response = {'id': str(audience_id)}
        response.update(data)

        return self.create_api_response(response)

    def _get_audience(self, request, account, audience_id):
        audiences = models.Audience.objects.filter(pk=audience_id).filter(pixel__account=account)
        if not audiences:
            raise exc.MissingDataError('Audience does not exist')

        audience = audiences[0]
        if not audience.pixel.account.users.filter(pk=request.user.pk).exists():
            raise exc.MissingDataError('Audience does not exist')

        rules = models.Rule.objects.filter(audience=audience)
        rules_dicts = []
        for rule in rules:
            rules_dicts.append({
                'id': rule.pk,
                'type': rule.type,
                'value': rule.value,
            })

        response = {
            'id': audience.pk,
            'name': audience.name,
            'pixel': audience.pixel.pk,
            'ttl': audience.ttl,
            'rules': rules_dicts,
        }
        return self.create_api_response(response)

    def _get_audiences(self, request, account):
        audiences = models.Audience.objects.filter(pixel__account=account).order_by('name')

        rows = []
        for audience in audiences:
            rows.append({
                'id': audience.pk,
                'name': audience.name,
                'count': 1000,  # TODO once sampling is done
                'count_yesterday': 100,  # TODO once sampling is done
                'created_dt': audience.created_dt,
            })

        return self.create_api_response(rows)


class AudienceArchive(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        # This is here to see if user has permissions for this account
        helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(pk=audience_id)
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError('Audience does not exist')

        audience.archived = True
        audience.save(
            request,
            constants.HistoryActionType.AUDIENCE_ARCHIVE,
            'Archived audience "{}".'.format(audience.name)
        )

        return self.create_api_response()


class AudienceRestore(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        # This is here to see if user has permissions for this account
        helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(pk=audience_id)
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError('Audience does not exist')

        audience.archived = False
        audience.save(
            request,
            constants.HistoryActionType.AUDIENCE_RESTORE,
            'Restored audience "{}".'.format(audience.name)
        )

        return self.create_api_response()
