from rest_framework import permissions

import core.features.audiences
import core.models
import restapi.access
import utils.exc
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class CanManageCustomAudiencesPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.account_custom_audiences_view"))


class AudienceViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, CanManageCustomAudiencesPermission)

    def get(self, request, account_id, audience_id):
        account = restapi.access.get_account(request.user, account_id)
        audience = self._get_audience(account, audience_id)
        return self.response_ok(serializers.AudienceSerializer(audience).data)

    def list(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        audiences = (
            core.features.audiences.Audience.objects.filter(pixel__account=account)
            .prefetch_related("audiencerule_set")
            .select_related("pixel__account")
            .order_by("name")
        )
        if request.GET.get("include_archived", "") != "1":
            audiences = audiences.filter(archived=False)
        return self.response_ok(serializers.AudienceSerializer(audiences, many=True).data)

    def put(self, request, account_id, audience_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.AudienceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        audience = self._get_audience(account, audience_id)
        try:
            audience.update(request, **serializer.validated_data)

        except core.features.audiences.audience.exceptions.CanNotArchive as err:
            raise utils.exc.ValidationError(errors={"archived": [str(err)]})

        return self.response_ok(serializers.AudienceSerializer(audience).data)

    def create(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.AudienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pixel = self._get_pixel(account, data["pixel_id"])
        try:
            new_audience = core.features.audiences.Audience.objects.create(
                request, data["name"], pixel, data["ttl"], data["ttl"], data["audiencerule_set"]
            )

        except (
            core.features.audiences.audience.exceptions.PixelIsArchived,
            core.features.audiences.audience.exceptions.RuleTtlCombinationAlreadyExists,
        ) as err:
            raise utils.exc.ValidationError(errors={"pixel_id": [str(err)]})

        except (
            core.features.audiences.audience.exceptions.RuleValueMissing,
            core.features.audiences.audience.exceptions.RuleUrlInvalid,
        ) as err:
            raise utils.exc.ValidationError(errors={"rules": [{"value": [str(err)]}]})

        return self.response_ok(serializers.AudienceSerializer(new_audience).data, status=201)

    @staticmethod
    def _get_audience(account, audience_id):
        try:
            audience = core.features.audiences.Audience.objects.get(pixel__account=account, id=audience_id)
        except core.features.audiences.Audience.DoesNotExist:
            raise utils.exc.MissingDataError("Audience does not exist!")
        return audience

    @staticmethod
    def _get_pixel(account, pixel_id):
        try:
            pixel = core.models.ConversionPixel.objects.get(account=account, id=pixel_id)
        except core.models.ConversionPixel.DoesNotExist:
            raise utils.exc.MissingDataError("Pixel does not exist!")
        return pixel
