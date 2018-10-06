from ..settings_query_set import SettingsQuerySet


class QuerySet(SettingsQuerySet):
    def latest_per_entity(self):
        return self.order_by("ad_group_id", "-created_dt").distinct("ad_group")

    def only_state_fields(self):
        """ Only select fields that are releant to calculating ad group state """

        return self.only("ad_group_id", "state", "start_date", "end_date")