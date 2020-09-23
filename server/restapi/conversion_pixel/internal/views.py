import functools

import rest_framework.permissions
from django.db.models import Q

import core.models
import utils.converters
import utils.exc
import zemauth.access
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class ConversionPixelViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.ConversionPixelSerializer
    create_serializer = serializers.ConversionPixelCreateSerializer

    def get(self, request, pixel_id):
        pixel = zemauth.access.get_conversion_pixel(request.user, Permission.READ, pixel_id)
        return self.response_ok(self.serializer(pixel, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.ConversionPixelQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            pixels = core.models.ConversionPixel.objects.filter(account=account)

        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            pixels = core.models.ConversionPixel.objects.filter(Q(account__agency=agency))

        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        keyword = qpe.validated_data.get("keyword")
        if keyword:
            pixels = pixels.filter(name__icontains=keyword)

        audience_enabled_only = utils.converters.x_to_bool(qpe.validated_data.get("audience_enabled_only"))
        if audience_enabled_only:
            pixels = pixels.filter(Q(audience_enabled=True) | Q(additional_pixel=True))

        serializer = self.serializer(pixels, many=True, context={"request": request})
        return self.response_ok(serializer.data)

    def put(self, request, pixel_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)

        pixel = zemauth.access.get_conversion_pixel(request.user, Permission.READ, pixel_id)
        pixel_update_fn = functools.partial(pixel.update, request, **serializer.validated_data)
        self._update_pixel(pixel_update_fn)
        return self.response_ok(self.serializer(pixel, context={"request": request}).data)

    def create(self, request):
        serializer = self.create_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account_id = data.get("account_id")
        account = (
            zemauth.access.get_account(request.user, Permission.WRITE, account_id) if account_id is not None else None
        )

        pixel_create_fn = functools.partial(
            core.models.ConversionPixel.objects.create, request, account, **serializer.validated_data
        )
        new_conversion_pixel = self._update_pixel(pixel_create_fn)
        return self.response_ok(self.serializer(new_conversion_pixel, context={"request": request}).data, status=201)

    @staticmethod
    def _update_pixel(pixel_update_fn):
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
