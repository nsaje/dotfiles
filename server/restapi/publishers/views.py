import restapi.views
import restapi.access
import dash.views.helpers
import core.publisher_groups.publisher_group_helpers
import dash.constants

import serializers


class PublishersViewList(restapi.views.RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        publisher_group_items = self._get_publisher_group_items(ad_group)
        bid_modifier_items = self._get_bid_modifier_items(ad_group)
        serializer = serializers.PublisherSerializer(bid_modifier_items + publisher_group_items, many=True)
        return self.response_ok(serializer.data)

    def _get_publisher_group_items(self, ad_group):
        targeting = core.publisher_groups.publisher_group_helpers.get_publisher_group_targeting_dict(
            ad_group, ad_group.get_current_settings(),
            ad_group.campaign, ad_group.campaign.get_current_settings(),
            ad_group.campaign.account, ad_group.campaign.account.get_current_settings(),
            include_global=False)

        publishers = []

        def add_entries(entries, level):
            for entry in entries:
                publishers.append({
                    'name': entry.publisher,
                    'source': entry.source,
                    'status': dash.constants.PublisherStatus.BLACKLISTED,
                    'level': level,
                })

        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting['ad_group']['excluded']).select_related('source'),
            dash.constants.PublisherBlacklistLevel.ADGROUP
        )
        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting['campaign']['excluded']).select_related('source'),
            dash.constants.PublisherBlacklistLevel.CAMPAIGN)
        add_entries(
            dash.models.PublisherGroupEntry.objects.filter(
                publisher_group_id__in=targeting['account']['excluded']).select_related('source'),
            dash.constants.PublisherBlacklistLevel.ACCOUNT)

        return publishers

    def _get_bid_modifier_items(self, ad_group):
        return []

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)  # validate ad group is allowed
        serializer = serializers.PublisherSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self._blacklist(request, ad_group, serializer.validated_data)
        return self.response_ok(serializer.initial_data)

    def _blacklist(self, request, ad_group, entries):
        for entry in entries:
            cleaned_entry = {
                'publisher': entry['name'],
                'source': entry['source'],
                'include_subdomains': True,
            }
            entity = self._get_level_entity(ad_group, entry)
            if entry['status'] == dash.constants.PublisherStatus.BLACKLISTED:
                core.publisher_groups.publisher_group_helpers.blacklist_publishers(request, [cleaned_entry], entity)
            elif entry['status'] == dash.constants.PublisherStatus.ENABLED:
                core.publisher_groups.publisher_group_helpers.unlist_publishers(request, [cleaned_entry], entity)

    @staticmethod
    def _get_level_entity(ad_group, entry):
        if entry['level'] == dash.constants.PublisherBlacklistLevel.ADGROUP:
            return ad_group
        elif entry['level'] == dash.constants.PublisherBlacklistLevel.CAMPAIGN:
            return ad_group.campaign
        elif entry['level'] == dash.constants.PublisherBlacklistLevel.ACCOUNT:
            return ad_group.campaign.account
        else:
            return None
