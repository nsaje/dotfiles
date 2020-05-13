from typing import List

from django.utils.functional import cached_property

import core.models
import utils
from core.features.publisher_groups import CONNECTION_NAMES_MAP
from dash import constants


class PublisherGroupMixin(object):
    @property
    def type(self):
        type_ = self.publisher_group_origin[0]
        return type_

    @property
    def level(self):
        level = self.publisher_group_origin[1]
        return level

    @property
    def level_id(self):
        obj = self.publisher_group_origin[2]
        return obj.id if obj else None

    @property
    def level_name(self):
        obj_name = self.publisher_group_origin[3]
        return obj_name

    @cached_property
    def publisher_group_origin(self):
        return core.features.publisher_groups.parse_default_publisher_group_origin(self)

    def save(self, request, *args, **kwargs):
        if request and request.user:
            self.modified_by = request.user
        self.full_clean()
        super().save(*args, **kwargs)

    def write_history(self, changes_text, changes, action_type, user=None, system_user=None):

        if not changes and not changes_text:
            return None

        account = self.account
        agency = self.agency
        level = constants.HistoryLevel.ACCOUNT if account else constants.HistoryLevel.AGENCY

        return core.features.history.History.objects.create(
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=changes,
            changes_text=changes_text or "",
            level=level,
            action_type=action_type,
        )

    def delete(self, request):
        usages = self._get_usages_of_publisher_group(request)
        if usages:
            raise utils.exc.ValidationError(
                "This publisher group can not be deleted, because it is " + ", ".join(usages) + "."
            )
        super().delete()

    def _get_usages_of_publisher_group(self, request):
        all_connections: List = core.features.publisher_groups.get_publisher_group_connections(
            request.user, self.id, True
        )
        all_connections_count: int = len(all_connections)
        user_connections: List = list(filter(lambda x: (x["user_access"]), all_connections))
        user_connections_count: int = len(user_connections)

        locations = []
        for connection in user_connections:
            location_name = CONNECTION_NAMES_MAP[connection["location"]]
            locations.append(location_name + ' "' + connection["name"] + '"')

        if user_connections_count < all_connections_count:
            if user_connections_count == 0:
                locations.append("used in " + str(all_connections_count) + " locations")
            else:
                diff = all_connections_count - user_connections_count
                locations.append("used in " + str(diff) + " other locations")

        return locations
