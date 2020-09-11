from rest_framework import permissions
from rest_framework import status

import core.features.bid_modifiers
import restapi.common.views_base
import zemauth.access
import zemauth.features.entity_permission.helpers
from core.features.bid_modifiers import create_bid_modifier_dict
from dash import models
from restapi.common import pagination
from utils import exc
from zemauth.features.entity_permission import Permission

from . import serializers


class BidModifierViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def _filter_bid_modifiers(self, ad_group_id, user, permission):
        user_permission_qs = models.BidModifier.objects.filter_by_user(user).filter(ad_group__id=ad_group_id)
        entity_permission_qs = models.BidModifier.objects.filter_by_entity_permission(user, permission).filter(
            ad_group__id=ad_group_id
        )
        return zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, user_permission_qs, entity_permission_qs
        )

    def list(self, request, ad_group_id):
        bid_modifiers = (
            self._filter_bid_modifiers(ad_group_id, request.user, Permission.READ)
            .select_related("source")
            .order_by("pk")
        )

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

        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        try:
            bid_modifier, _ = core.features.bid_modifiers.set(
                ad_group,
                input_data["type"],
                input_data["target"],
                self._source_from_source_slug(input_data.get("source_slug")),
                input_data["modifier"],
                user=request.user,
            )

        except core.features.bid_modifiers.BidModifierInvalid as e:
            raise exc.ValidationError(str(e))

        except core.features.bid_modifiers.BidModifierTargetAdGroupMismatch as e:
            raise exc.ValidationError(errors={"target": [str(e)]})

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, ad_group_id, pk=None):
        try:
            bid_modifier = (
                self._filter_bid_modifiers(ad_group_id, request.user, Permission.READ)
                .select_related("source")
                .get(pk=pk)
            )
        except models.BidModifier.DoesNotExist:
            raise exc.MissingDataError("Bid Modifier does not exist")

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data)

    def update(self, request, ad_group_id, pk=None):
        bid_modifier = models.BidModifier.objects.filter(id=pk).first()
        serializer = serializers.BidModifierSerializer(instance=bid_modifier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        input_data = serializer.validated_data

        try:
            bid_modifier = (
                self._filter_bid_modifiers(ad_group_id, request.user, Permission.WRITE)
                .select_related("source")
                .get(id=pk)
            )
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

        if bid_modifier is None:
            bid_modifier_dict = create_bid_modifier_dict(
                None,
                modifier_type=serializer.instance.type,
                target=serializer.instance.target,
                source_slug=serializer.instance.source_slug,
            )
            bid_modifier = models.BidModifier(**bid_modifier_dict)

        return self.response_ok(serializers.BidModifierSerializer(bid_modifier).data)

    def update_bulk(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        serializer = serializers.BidModifierSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        input_data = serializer.validated_data

        bms_to_set = [
            core.features.bid_modifiers.BidModifierData(
                type=bm["type"],
                target=bm["target"],
                source=self._source_from_source_slug(bm.get("source_slug")),
                modifier=bm["modifier"],
            )
            for bm in input_data
        ]
        try:
            bid_modifiers = core.features.bid_modifiers.set_bulk(ad_group, bms_to_set, user=request.user)

        except (
            core.features.bid_modifiers.BidModifierInvalid,
            core.features.bid_modifiers.BidModifierTargetAdGroupMismatch,
        ) as e:
            raise exc.ValidationError(str(e))

        return self.response_ok(serializers.BidModifierSerializer(bid_modifiers, many=True).data)

    @staticmethod
    def _source_from_source_slug(source_slug):
        if source_slug:
            try:
                return models.Source.objects.get(bidder_slug=source_slug)
            except models.Source.DoesNotExist:
                raise exc.MissingDataError("Source does not exist")
        return None

    def destroy(self, request, ad_group_id, pk=None):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        if pk is not None:
            self._delete_single(request, ad_group, pk)
        else:
            self._delete_multiple(request, ad_group)

        return self.response_ok({}, status=status.HTTP_204_NO_CONTENT)

    def _delete_single(self, request, ad_group, pk):
        if request.data:
            raise exc.ValidationError("Delete Bid Modifier requires no data")

        try:
            core.features.bid_modifiers.delete(ad_group, [int(pk)], user=request.user)
        except core.features.bid_modifiers.BidModifierDeleteInvalidIds:
            raise exc.MissingDataError("Bid Modifier does not exist")

    def _delete_multiple(self, request, ad_group):
        if not request.data:
            raise exc.ValidationError("Provide Bid Modifiers to delete")

        serializer = serializers.BidModifierIdSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        bid_modifier_ids = [e["id"] for e in serializer.validated_data]

        try:
            core.features.bid_modifiers.delete(ad_group, bid_modifier_ids, user=request.user)
        except core.features.bid_modifiers.BidModifierDeleteInvalidIds as e:
            raise exc.ValidationError(str(e))
