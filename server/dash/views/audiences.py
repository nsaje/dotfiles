import json

import core.features.audiences.audience.exceptions
import redshiftapi.api_audiences
from dash import forms
from dash import models
from utils import api_common
from utils import exc

from . import helpers


class AudiencesView(api_common.BaseApiView):
    def get(self, request, account_id, audience_id=None):
        if not request.user.has_perm("zemauth.account_custom_audiences_view"):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        if audience_id:
            audience_id = int(audience_id)

        account = helpers.get_account(request.user, account_id)

        if audience_id:
            return self._get_audience(request, account, audience_id)

        return self._get_audiences(request, account)

    def post(self, request, account_id):
        if not request.user.has_perm("zemauth.account_custom_audiences_view"):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)

        resource = json.loads(request.body)
        audience_form = forms.AudienceForm(account, request.user, resource)
        if not audience_form.is_valid():
            raise exc.ValidationError(errors=dict(audience_form.errors))

        try:
            pixel = models.ConversionPixel.objects.get(pk=audience_form.cleaned_data["pixel_id"], account=account)
        except models.ConversionPixel.DoesNotExist:
            raise exc.MissingDataError("Pixel does not exist.")

        try:
            audience = models.Audience.objects.create(
                request,
                audience_form.cleaned_data["name"],
                pixel,
                audience_form.cleaned_data["ttl"],
                audience_form.cleaned_data["ttl"],  # prefill days is an internal feature with isn't currently in use
                audience_form.cleaned_data["rules"],
            )

        except (
            core.features.audiences.audience.exceptions.PixelIsArchived,
            core.features.audiences.audience.exceptions.RuleTtlCombinationAlreadyExists,
        ) as err:
            raise exc.ValidationError(errors={"pixel_id": [str(err)]})

        except (
            core.features.audiences.audience.exceptions.RuleValueMissing,
            core.features.audiences.audience.exceptions.RuleUrlInvalid,
        ) as err:
            raise exc.ValidationError(errors={"rules": [str(err)]})

        rules = models.AudienceRule.objects.filter(audience=audience)
        response = self._get_response_dict(audience, rules)

        return self.create_api_response(response)

    def put(self, request, account_id, audience_id):
        if not request.user.has_perm("zemauth.account_custom_audiences_view"):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        account = helpers.get_account(request.user, account_id)

        audiences = models.Audience.objects.filter(pk=audience_id).filter(pixel__account=account)
        if not audiences:
            raise exc.MissingDataError("Audience does not exist")
        audience = audiences[0]

        resource = json.loads(request.body)
        audience_form = forms.AudienceUpdateForm(resource)
        if not audience_form.is_valid():
            raise exc.ValidationError(errors=dict(audience_form.errors))

        data = audience_form.cleaned_data
        audience.update(request, name=data.get("name"))
        rules = models.AudienceRule.objects.filter(audience=audience)

        return self.create_api_response(self._get_response_dict(audience, rules))

    def _get_audience(self, request, account, audience_id):
        audiences = models.Audience.objects.filter(pk=audience_id).filter(pixel__account=account)
        if not audiences:
            raise exc.MissingDataError("Audience does not exist")

        audience = audiences[0]
        rules = models.AudienceRule.objects.filter(audience=audience)

        return self.create_api_response(self._get_response_dict(audience, rules))

    def _get_audiences(self, request, account):
        audiences = (
            models.Audience.objects.filter(pixel__account=account)
            .prefetch_related("audiencerule_set")
            .select_related("pixel__account")
            .order_by("name")
        )

        if request.GET.get("include_archived", "") != "1":
            audiences = audiences.filter(archived=False)

        include_size = request.GET.get("include_size", "") == "1"

        rows = []
        for audience in audiences:
            count = None
            count_yesterday = None

            if include_size:
                rules = audience.audiencerule_set.all()
                count = (
                    redshiftapi.api_audiences.get_audience_sample_size(
                        audience.pixel.account.id, audience.pixel.slug, audience.ttl, rules
                    )
                    * 100
                )
                count_yesterday = (
                    redshiftapi.api_audiences.get_audience_sample_size(
                        audience.pixel.account.id, audience.pixel.slug, 1, rules
                    )
                    * 100
                )

            rows.append(
                {
                    "id": str(audience.pk),
                    "name": audience.name,
                    "count": count,
                    "count_yesterday": count_yesterday,
                    "archived": audience.archived,
                    "created_dt": audience.created_dt,
                }
            )

        return self.create_api_response(rows)

    def _get_response_dict(self, audience, rules):
        if not audience or not rules:
            return {}

        rules_dicts = []
        for rule in rules:
            rules_dicts.append({"id": str(rule.pk), "type": rule.type, "value": rule.value})

        response = {
            "id": str(audience.pk),
            "name": audience.name,
            "pixel_id": str(audience.pixel.pk),
            "ttl": audience.ttl,
            "prefill_days": audience.prefill_days,
            "rules": rules_dicts,
        }

        return response


class AudienceArchive(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm("zemauth.account_custom_audiences_view"):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        # This is here to see if user has permissions for this account
        account = helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(pk=audience_id, pixel__account=account)
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError("Audience does not exist")

        try:
            audience.update(request, archived=True)
        except core.features.audiences.audience.exceptions.CanNotArchive as err:
            raise exc.ValidationError(errors=str(err))

        return self.create_api_response()


class AudienceRestore(api_common.BaseApiView):
    def post(self, request, account_id, audience_id):
        if not request.user.has_perm("zemauth.account_custom_audiences_view"):
            raise exc.AuthorizationError()

        account_id = int(account_id)
        audience_id = int(audience_id)

        # This is here to see if user has permissions for this account
        account = helpers.get_account(request.user, account_id)

        audience = None
        try:
            audience = models.Audience.objects.get(pk=audience_id, pixel__account=account)
        except models.Audience.DoesNotExist:
            raise exc.MissingDataError("Audience does not exist")

        audience.update(request, archived=False)
        return self.create_api_response()
