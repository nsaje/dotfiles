import restapi.conversion_pixel.v1.serializers


class ConversionPixelSerializer(restapi.conversion_pixel.v1.serializers.ConversionPixelSerializer):
    pass


class ConversionPixelCreateSerializer(restapi.conversion_pixel.v1.serializers.ConversionPixelCreateSerializer):
    account_id = restapi.serializers.fields.IdField(required=True)


class ConversionPixelQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(max_length=50, required=False)
    audience_enabled_only = restapi.serializers.fields.NullBooleanField(required=False)
