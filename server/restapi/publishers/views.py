from django.db import transaction
from rest_framework import permissions

import core.features.publisher_bid_modifiers
import core.features.publisher_bid_modifiers.exceptions
import core.features.publisher_groups.publisher_group_helpers
import dash.constants
import dash.views.helpers
import restapi.access
import restapi.common.views_base

from . import serializers


class PublishersViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        items = self._get_publisher_group_items(ad_group)
        items = self._augment_with_bid_modifiers(items, ad_group)
        serializer = serializers.PublisherSerializer(items, many=True)
        return self.response_ok(serializer.data)

    def _get_publisher_group_items(self, ad_group):
        targeting = core.features.publisher_groups.publisher_group_helpers.get_publisher_group_targeting_dict(
            ad_group,
            ad_group.get_current_settings(),
            ad_group.campaign,
            ad_group.campaign.get_current_settings(),
            ad_group.campaign.account,
            ad_group.campaign.account.get_current_settings(),
            include_global=False,
        )

        publishers = []

        def add_entries(entries, level):
            for entry in entries:
                publishers.append(
                    {
                        "name": entry.publisher,
                        "source": entry.source,
                        "status": dash.constants.PublisherStatus.BLACKLISTED,
                        "level": level,
                    }
                )

        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["ad_group"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.ADGROUP,
        )
        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["campaign"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.CAMPAIGN,
        )
        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["account"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.ACCOUNT,
        )

        return publishers

    def _augment_with_bid_modifiers(self, items, ad_group):
        modifiers = core.features.publisher_bid_modifiers.get(ad_group)
        modifiers_by_publisher_source = {(m["publisher"], m["source"]): m for m in modifiers}
        remaining_modifiers_keys = set(modifiers_by_publisher_source.keys())

        for item in items:
            publisher_source_key = (item["name"], item["source"])
            modifier = modifiers_by_publisher_source.get(publisher_source_key)
            if not modifier or item["level"] != dash.constants.PublisherBlacklistLevel.ADGROUP:
                continue
            item["modifier"] = modifier["modifier"]
            remaining_modifiers_keys.discard(publisher_source_key)

        for publisher_source_key in sorted(remaining_modifiers_keys, key=lambda x: (x[0], x[1].name)):
            modifier = modifiers_by_publisher_source[publisher_source_key]
            items.append(
                {
                    "name": modifier["publisher"],
                    "source": modifier["source"],
                    "status": dash.constants.PublisherStatus.ENABLED,
                    "level": dash.constants.PublisherBlacklistLevel.ADGROUP,
                    "modifier": modifier["modifier"],
                }
            )

        return items

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)  # validate ad group is allowed
        serializer = serializers.PublisherSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self._put_handle_entries(request, ad_group, serializer.validated_data)
        return self.response_ok(serializer.data)

    @transaction.atomic()
    def _put_handle_entries(self, request, ad_group, entries):
        for entry in entries:
            cleaned_entry = {"publisher": entry["name"], "source": entry["source"], "include_subdomains": True}
            entity = self._get_level_entity(ad_group, entry)
            if entry["status"] == dash.constants.PublisherStatus.BLACKLISTED:
                core.features.publisher_groups.publisher_group_helpers.blacklist_publishers(
                    request, [cleaned_entry], entity
                )
            elif entry["status"] == dash.constants.PublisherStatus.ENABLED:
                core.features.publisher_groups.publisher_group_helpers.unlist_publishers(
                    request, [cleaned_entry], entity
                )

            if entry["level"] == dash.constants.PublisherBlacklistLevel.ADGROUP:
                bid_modifier = entry.get("modifier")
                try:
                    core.features.publisher_bid_modifiers.set(
                        ad_group, entry["name"], entry["source"], bid_modifier, user=request.user
                    )
                except core.features.publisher_bid_modifiers.exceptions.BidModifierInvalid:
                    raise serializers.ValidationError({"modifier": "Bid modifier invalid!"})

    @staticmethod
    def _get_level_entity(ad_group, entry):
        if entry["level"] == dash.constants.PublisherBlacklistLevel.ADGROUP:
            return ad_group
        elif entry["level"] == dash.constants.PublisherBlacklistLevel.CAMPAIGN:
            return ad_group.campaign
        elif entry["level"] == dash.constants.PublisherBlacklistLevel.ACCOUNT:
            return ad_group.campaign.account
        else:
            return None
