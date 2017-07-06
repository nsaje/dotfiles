import json

from django.db import transaction

from dash import constants
from dash import forms
from dash import models
import redshiftapi.api_audiences
from utils import api_common
from utils import exc
from utils import k1_helper
from utils import redirector_helper
import helpers


class AudiencesView(api_common.BaseApiView):
    def get(self, request, account_id, audience_id=None):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        if audience_id:
            audience_id = int(audience_id)

        account = helpers.get_account(request.user, account_id)

        if audience_id:
            return self._get_audience(request, account, audience_id)

        return self._get_audiences(request, account)

    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)

        resource = json.loads(request.body)
        audience_form = forms.AudienceForm(account, request.user, resource)
        if not audience_form.is_valid():
            raise exc.ValidationError(errors=dict(audience_form.errors))

        data = audience_form.cleaned_data

        audience = None
        refererRules = (constants.AudienceRuleType.CONTAINS, constants.AudienceRuleType.STARTS_WITH)
        with transaction.atomic():
            audience = models.Audience(
                name=data['name'],
                pixel_id=data['pixel_id'],
                ttl=data['ttl'],
            )
            audience.save(
                request,
                constants.HistoryActionType.AUDIENCE_CREATE,
                u'Created audience "{}".'.format(audience.name)
            )

            for rule in audience_form.cleaned_data['rules']:
                value = rule['value'] or ''
                if rule['type'] in refererRules:
                    value = ','.join([x.strip() for x in value.split(',') if x])

                rule = models.AudienceRule(
                    audience=audience,
                    type=rule['type'],
                    value=value,
                )
                rule.save()

            redirector_helper.upsert_audience(audience)

        k1_helper.update_account(account_id, msg="audience.create")

        response = self._get_response_dict(audience, [rule])

        return self.create_api_response(response)

    def put(self, request, account_id, audience_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        account = helpers.get_account(request.user, account_id)

        audiences = models.Audience.objects.filter(pk=audience_id).filter(pixel__account=account)
        if not audiences:
            raise exc.MissingDataError('Audience does not exist')
        audience = audiences[0]

        resource = json.loads(request.body)
        audience_form = forms.AudienceUpdateForm(resource)
        if not audience_form.is_valid():
            raise exc.ValidationError(errors=dict(audience_form.errors))

        data = audience_form.cleaned_data

        old_name = audience.name
        if audience.name != data['name']:
            audience.name = data['name']

            with transaction.atomic():
                audience.save(
                    request,
                    constants.HistoryActionType.AUDIENCE_UPDATE,
                    u'Changed audience name from "{}" to "{}".'.format(old_name, audience.name)
                )
                redirector_helper.upsert_audience(audience)

            k1_helper.update_account(account_id, msg="audience.update")

        rules = models.AudienceRule.objects.filter(audience=audience)

        return self.create_api_response(self._get_response_dict(audience, rules))

    def _get_audience(self, request, account, audience_id):
        audiences = models.Audience.objects.filter(pk=audience_id).filter(pixel__account=account)
        if not audiences:
            raise exc.MissingDataError('Audience does not exist')

        audience = audiences[0]
        rules = models.AudienceRule.objects.filter(audience=audience)

        return self.create_api_response(self._get_response_dict(audience, rules))

    def _get_audiences(self, request, account):
        audiences = models.Audience.objects.filter(pixel__account=account).order_by('name')

        if request.GET.get('include_archived', '') != '1':
            audiences = audiences.filter(archived=False)

        include_size = request.GET.get('include_size', '') == '1'

        count = None
        count_yesterday = None
        rows = []
        for audience in audiences:
            if False and include_size:
                count = redshiftapi.api_audiences.get_audience_sample_size(
                    audience.pixel.account.id,
                    audience.pixel.slug,
                    audience.ttl,
                    audience.audiencerule_set.all()) * 100
                count_yesterday = redshiftapi.api_audiences.get_audience_sample_size(
                    audience.pixel.account.id,
                    audience.pixel.slug,
                    1,
                    audience.audiencerule_set.all()) * 100

            rows.append({
                'id': str(audience.pk),
                'name': audience.name,
                'count': 'N/A',
                'count_yesterday': 'N/A',
                'archived': audience.archived,
                'created_dt': audience.created_dt,
            })

        return self.create_api_response(rows)

    def _get_response_dict(self, audience, rules):
        if not audience or not rules:
            return {}

        rules_dicts = []
        for rule in rules:
            rules_dicts.append({
                'id': str(rule.pk),
                'type': rule.type,
                'value': rule.value,
            })

        response = {
            'id': str(audience.pk),
            'name': audience.name,
            'pixel_id': str(audience.pixel.pk),
            'ttl': audience.ttl,
            'rules': rules_dicts,
        }

        return response


class AudienceArchive(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        # This is here to see if user has permissions for this account
        account = helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(
                pk=audience_id,
                pixel__account=account
            )
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError('Audience does not exist')

        audience.archived = True
        with transaction.atomic():
            audience.save(
                request,
                constants.HistoryActionType.AUDIENCE_ARCHIVE,
                u'Archived audience "{}".'.format(audience.name)
            )
            redirector_helper.upsert_audience(audience)

        return self.create_api_response()


class AudienceRestore(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm('zemauth.account_custom_audiences_view'):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        # This is here to see if user has permissions for this account
        account = helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(
                pk=audience_id,
                pixel__account=account
            )
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError('Audience does not exist')

        audience.archived = False
        with transaction.atomic():
            audience.save(
                request,
                constants.HistoryActionType.AUDIENCE_RESTORE,
                u'Restored audience "{}".'.format(audience.name)
            )
            redirector_helper.upsert_audience(audience)

        return self.create_api_response()
