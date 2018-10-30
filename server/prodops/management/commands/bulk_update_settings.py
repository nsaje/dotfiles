from django.db.models import Q

import utils.command_helpers
from dash import models


class Command(utils.command_helpers.ExceptionCommand):
    help = """Bulk update adgroup settings for the entity provided."""

    def add_arguments(self, parser):
        parser.add_argument(
            "adgroup_setting",
            type=str,
            choices=models.AdGroupSettings.get_settings_fields(),
            help="Ad group setting to update",
        )
        parser.add_argument("setting_value", help="Value to set on the adgroup setting.")
        parser.add_argument("--agencies", default="")
        parser.add_argument("--accounts", default="")
        parser.add_argument("--campaigns", default="")
        parser.add_argument("--ad-groups", default="")
        parser.add_argument(
            "--unsafe", action="store_true", default=False, help="Run the update_unsafe method on settings."
        )

    def _clean_ids(self, raw):
        return raw and set(map(int, [x.strip() for x in raw.split(",") if x.strip()])) or set()

    def handle(self, *args, **options):
        agency_ids = self._clean_ids(options["agencies"])
        account_ids = self._clean_ids(options["accounts"])
        campaign_ids = self._clean_ids(options["campaigns"])
        ad_group_ids = self._clean_ids(options["ad_groups"])
        setting = options.get("adgroup_setting")
        setting_value = options.get("setting_value")

        ad_groups = models.AdGroup.objects.filter(
            Q(pk__in=ad_group_ids)
            | Q(campaign_id__in=campaign_ids)
            | Q(campaign__account_id__in=account_ids)
            | Q(campaign__account__agency_id__in=agency_ids)
        ).exclude(**{"settings__{}".format(setting): setting_value})

        kwargs = {setting: setting_value}
        if not ad_groups:
            self.stdout.write("No ad groups found for the given IDs")
            return
        for adg in ad_groups:
            self.stdout.write(
                "Ad group with id '{}' have setting '{}' set to '{}'".format(
                    adg.id, setting, getattr(adg.settings, setting)
                )
            )
            if options.get("unsafe"):
                adg.settings.update_unsafe(None, **kwargs)
            else:
                adg.settings.update(None, **kwargs)
            self.stdout.write(
                "ad group with id '{}' had setting '{}' changed to '{}'".format(adg.id, setting, setting_value)
            )
