from rest_framework import permissions
from rest_framework import status

import core.features.bid_modifiers
import restapi.access
import restapi.common.views_base
from dash import models
from restapi.common import pagination
from restapi.common import permissions as restapi_permissions
from utils import exc

from . import serializers


class BidModifierViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def _filter_bid_modifiers(self, ad_group_id, user):
        return (
            models.BidModifier.objects.filter_by_user(user).filter(ad_group__id=ad_group_id)
            # TEMP(tkusterle) temporarily disable source bid modifiers
            .exclude(type=core.features.bid_modifiers.BidModifierType.SOURCE)
        )

    def list(self, request, ad_group_id):
        bid_modifiers = self._filter_bid_modifiers(ad_group_id, request.user).select_related("source").order_by("pk")

        if "type" in request.GET:
            modifier_type = core.features.bid_modifiers.BidModifierType.get_constant_value(request.GET["type"])
            if modifier_type:
                bid_modifiers = bid_modifiers.filter(type=modifier_type)
            else:
                bid_modifiers = models.BidModifier.objects.none()

        paginator = pagination.StandardPagination()
        paginated_bid_modifiers = paginator.paginate_queryset(bid_modifiers, request)
        return paginator.get_paginated_response(
            serializers.BidModifierSerializer(paginated_bid_modifiers, many=True).data
        )

    def create(self, request, ad_group_id):
        serializer = serializers.BidModifierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        input_data = serializer.validated_data

        # TEMP(tkusterle) temporarily disable source bid modifiers
        if input_data["type"] == core.features.bid_modifiers.BidModifierType.SOURCE:
            raise exc.ValidationError("Source bid modifiers are temporarily disabled")

        try:
            ad_group = models.AdGroup.objects.filter_by_user(request.user).get(id=ad_group_id)
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError("Ad Group does not exist")

        if "source_slug" in input_data and input_data["source_slug"]:
            try:
                source = models.Source.objects.get(bidder_slug=input_data["source_slug"])
            except models.Source.DoesNotExist:
                raise exc.MissingDataError("Source does not exist")
        else:
            source = None

        try:
            bid_modifier, _ = core.features.bid_modifiers.set(
                ad_group, input_data["type"], input_data["target"], source, input_data["modifier"], user=request.user
            )
        except core.features.bid_modifiers.BidModifierInvalid as e:
            raise exc.ValidationError(str(e))

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, ad_group_id, pk=None):
        try:
            bid_modifier = self._filter_bid_modifiers(ad_group_id, request.user).select_related("source").get(pk=pk)
        except models.BidModifier.DoesNotExist:
            raise exc.MissingDataError("Bid Modifier does not exist")

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data)

    def update(self, request, ad_group_id, pk=None):
        bid_modifier = models.BidModifier.objects.filter(id=pk).first()
        serializer = serializers.BidModifierSerializer(instance=bid_modifier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        input_data = serializer.validated_data

        try:
            bid_modifier = self._filter_bid_modifiers(ad_group_id, request.user).select_related("source").get(id=pk)
        except models.BidModifier.DoesNotExist:
            raise exc.MissingDataError("Bid Modifier does not exist")

        bid_modifier, _ = core.features.bid_modifiers.set(
            bid_modifier.ad_group,
            bid_modifier.type,
            bid_modifier.target,
            bid_modifier.source,
            input_data["modifier"],
            user=request.user,
        )

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data)

    def destroy(self, request, ad_group_id, pk=None):

        if pk is not None:
            if request.data:
                raise exc.ValidationError("Delete Bid Modifier requires no data")

            number_of_deleted, _ = self._filter_bid_modifiers(ad_group_id, request.user).filter(id=pk).delete()

            if number_of_deleted > 0:
                return self.response_ok({}, status=status.HTTP_204_NO_CONTENT)

            raise exc.MissingDataError("Bid Modifier does not exist")

        else:
            bid_modifier_qs = models.BidModifier.objects.filter_by_user(request.user).filter(ad_group__id=ad_group_id)

            if not isinstance(request.data, dict) or request.data:
                # in case request data is not an empty dictionary validate it
                serializer = serializers.BidModifierIdSerializer(data=request.data, many=True)
                serializer.is_valid(raise_exception=True)
                input_id_set = set(e["id"] for e in serializer.validated_data)

                bid_modifier_ids = bid_modifier_qs.filter(id__in=input_id_set).values_list("id", flat=True)

                if set(bid_modifier_ids).symmetric_difference(input_id_set):
                    raise exc.ValidationError("Invalid Bid Modifier ids")

                bid_modifier_qs = models.BidModifier.objects.filter(id__in=input_id_set)

            bid_modifier_qs.delete()
            return self.response_ok({}, status=status.HTTP_204_NO_CONTENT)
