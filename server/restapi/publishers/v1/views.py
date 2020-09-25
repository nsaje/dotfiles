from collections import defaultdict

from django.db import transaction
from rest_framework import permissions

import core.features.bid_modifiers
import core.features.publisher_groups.service
import dash.constants
import dash.views.helpers
import restapi.common.views_base
import zemauth.access
from restapi.publishers.v1 import serializers
from utils import exc
from utils import k1_helper
from zemauth.features.entity_permission import Permission


class PublishersViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        items = self._get_publisher_group_items(ad_group, request.user)
        items = self._augment_with_bid_modifiers(items, ad_group)
        serializer = serializers.PublisherSerializer(items, many=True, context={"request": request})
        return self.response_ok(serializer.data)

    def _get_publisher_group_items(self, ad_group, user):
        targeting = core.features.publisher_groups.service.get_publisher_group_targeting_dict(
            ad_group,
            ad_group.get_current_settings(),
            ad_group.campaign,
            ad_group.campaign.get_current_settings(),
            ad_group.campaign.account,
            ad_group.campaign.account.get_current_settings(),
            include_global=False,
        )

        publishers = []

        def add_entries(user, entries, level):
            for entry in entries:
                publisher = {
                    "name": entry.publisher,
                    "source": entry.source,
                    "status": dash.constants.PublisherStatus.BLACKLISTED,
                    "level": level,
                    "placement": entry.placement,
                }

                publishers.append(publisher)

        add_entries(
            user,
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["ad_group"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.ADGROUP,
        )
        add_entries(
            user,
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["campaign"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.CAMPAIGN,
        )
        add_entries(
            user,
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting["account"]["excluded"]
            ).select_related("source"),
            dash.constants.PublisherBlacklistLevel.ACCOUNT,
        )

        return publishers

    def _augment_with_bid_modifiers(self, items, ad_group):
        modifiers = core.features.bid_modifiers.get(
            ad_group, include_types=[core.features.bid_modifiers.BidModifierType.PUBLISHER]
        )
        modifiers_by_publisher_source = {(m["target"], m["source"]): m for m in modifiers}
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
                    "name": modifier["target"],
                    "source": modifier["source"],
                    "status": dash.constants.PublisherStatus.ENABLED,
                    "level": dash.constants.PublisherBlacklistLevel.ADGROUP,
                    "modifier": modifier["modifier"],
                }
            )

        return items

    def put(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(
            request.user, Permission.WRITE, ad_group_id
        )  # validate ad group is allowed
        serializer = serializers.PublisherSerializer(data=request.data, many=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self._put_handle_entries(request, ad_group, serializer.validated_data)
        k1_helper.update_ad_group(ad_group, msg="restapi.publishers.set", priority=True)
        return self.response_ok(serializer.data)

    @transaction.atomic()
    def _put_handle_entries(self, request, ad_group, entries):
        entry_map = {
            dash.constants.PublisherStatus.BLACKLISTED: defaultdict(list),
            dash.constants.PublisherStatus.ENABLED: defaultdict(list),
        }
        bid_modifier_list = []

        for entry in entries:
            cleaned_entry = {"publisher": entry["name"], "source": entry["source"], "include_subdomains": True}
            entity = self._get_level_entity(ad_group, entry)
            entry_map[entry["status"]][entity].append(cleaned_entry)

            if entry["level"] == dash.constants.PublisherBlacklistLevel.ADGROUP:
                # TODO: BID MODIFIERS: DEPRECATED; need to make a plan to remove this completely
                if entry.get("source") is not None and "modifier" in entry:
                    try:
                        bid_modifier_list.append(
                            core.features.bid_modifiers.BidModifierData(
                                core.features.bid_modifiers.BidModifierType.PUBLISHER,
                                core.features.bid_modifiers.ApiConverter.to_target(
                                    core.features.bid_modifiers.BidModifierType.PUBLISHER, entry["name"]
                                ),
                                entry["source"],
                                entry.get("modifier"),
                            )
                        )
                    except core.features.bid_modifiers.BidModifierInvalid as e:
                        raise exc.ValidationError({"modifier": str(e)})

        for entity, cleaned_entries in entry_map[dash.constants.PublisherStatus.BLACKLISTED].items():
            core.features.publisher_groups.service.blacklist_publishers(request, cleaned_entries, entity)

        for entity, cleaned_entries in entry_map[dash.constants.PublisherStatus.ENABLED].items():
            core.features.publisher_groups.service.unlist_publishers(request, cleaned_entries, entity)

        if bid_modifier_list:
            core.features.bid_modifiers.set_bulk(ad_group, bid_modifier_list, user=request.user, propagate_to_k1=False)

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
