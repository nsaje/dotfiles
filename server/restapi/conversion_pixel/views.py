import functools

from django.db.models import Q

import core.models
import restapi.access
import utils.converters
import utils.exc
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class ConversionPixelViewSet(RESTAPIBaseViewSet):
    def get(self, request, account_id, pixel_id):
        account = restapi.access.get_account(request.user, account_id)
        pixel = self._get_pixel(account, pixel_id)
        return self.response_ok(serializers.ConversionPixelSerializer(pixel, context={"request": request}).data)

    def list(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        audience_enabled_only = utils.converters.x_to_bool(request.GET.get("audienceEnabledOnly"))
        pixels = core.models.ConversionPixel.objects.filter(account=account)
        if audience_enabled_only:
            pixels = pixels.filter(Q(audience_enabled=True) | Q(additional_pixel=True))
        serializer = serializers.ConversionPixelSerializer(pixels, many=True, context={"request": request})
        return self.response_ok(serializer.data)

    def put(self, request, account_id, pixel_id):
        account = restapi.access.get_account(request.user, account_id)
        pixel = self._get_pixel(account, pixel_id)
        serializer = serializers.ConversionPixelSerializer(
            data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        pixel_update_fn = functools.partial(pixel.update, request, **serializer.validated_data)
        self._update_pixel(pixel_update_fn)
        return self.response_ok(serializers.ConversionPixelSerializer(pixel, context={"request": request}).data)

    def create(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.ConversionPixelCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        pixel_create_fn = functools.partial(
            core.models.ConversionPixel.objects.create, request, account, **serializer.validated_data
        )
        new_conversion_pixel = self._update_pixel(pixel_create_fn)
        return self.response_ok(
            serializers.ConversionPixelSerializer(new_conversion_pixel, context={"request": request}).data, status=201
        )

    @staticmethod
    def _get_pixel(account, pixel_id):
        try:
            pixel = core.models.ConversionPixel.objects.get(account=account, id=pixel_id)
        except core.models.ConversionPixel.DoesNotExist:
            raise utils.exc.MissingDataError("Conversion pixel does not exist!")
        return pixel

    def _update_pixel(self, pixel_update_fn):
        try:
            return pixel_update_fn()

        except core.models.conversion_pixel.exceptions.DuplicatePixelName as err:
            raise utils.exc.ValidationError(errors={"name": [str(err)]})

        except core.models.conversion_pixel.exceptions.AudiencePixelAlreadyExists as err:
            raise utils.exc.ValidationError(errors={"audience_enabled": [str(err)]})

        except core.models.conversion_pixel.exceptions.AudiencePixelCanNotBeArchived as err:
            raise utils.exc.ValidationError(errors={"audience_enabled": [str(err)]})

        except core.models.conversion_pixel.exceptions.MutuallyExclusivePixelFlagsEnabled as err:
            raise utils.exc.ValidationError(errors={"additional_pixel": [str(err)]})

        except core.models.conversion_pixel.exceptions.AudiencePixelNotSet as err:
            raise utils.exc.ValidationError(errors={"additional_pixel": [str(err)]})
