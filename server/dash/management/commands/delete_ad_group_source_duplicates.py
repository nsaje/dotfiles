from collections import defaultdict

from django.db import connections
from django.db.models import Count
from django.db.models import Q

from automation import models as automation_models
from dash import models
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    help = "Find and delete AdGroupSource duplicates (before introducing DB constraints)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", dest="dry_run", action="store_true", help="Perform a dry run without making changes"
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if not dry_run:
            self.stdout.write(self.style.WARNING("Not in dry-run mode. DB records will be altered!"))

        duplicates = sorted(
            models.AdGroup.objects.all()
            .values("id")
            .annotate(id_count=Count("id"))
            .values("id", "adgroupsource__source__id", "id_count")
            .order_by("-id_count")
            .filter(id_count__gt=1),
            key=lambda x: x["id"],
        )

        if len(duplicates) < 1:
            self.stdout.write(self.style.SUCCESS("Found no duplicates! ;-)"))
            return

        self.stdout.write(self.style.WARNING("Found {} duplicates:".format(len(duplicates))))
        for e in duplicates:
            self.stdout.write(
                "ad_group_id: {}, source_id: {}, count: {}\n".format(
                    e["id"], e["adgroupsource__source__id"], e["id_count"]
                )
            )

        self.stdout.write("Duplicates belong to the following accounts:\n")
        for account in models.Account.objects.filter(
            campaign__adgroup__id__in=[e["id"] for e in duplicates]
        ).distinct():
            self.stdout.write("{}\n".format(account))

        condition_list = [
            Q(ad_group_source__ad_group__id=e["id"], ad_group_source__source__id=e["adgroupsource__source__id"])
            for e in duplicates
        ]
        condition_expression = Q()
        for condition in condition_list:
            condition_expression |= condition

        settings_list = list(models.AdGroupSourceSettings.objects.filter(condition_expression))
        self.stdout.write("Found {} related AdGroupSourceSettings objects\n".format(len(duplicates)))

        ad_group_source_qs = models.AdGroupSource.objects.filter(settings__id__in=[e.id for e in settings_list])

        running_ad_group_sources = set(ad_group_source_qs.filter_running().values_list("id", flat=True))

        if running_ad_group_sources:
            self.stdout.write("Found {} running AdGroupSource objects\n".format(len(running_ad_group_sources)))
            self.stdout.write("IDs of running AdGroupSource objects: {}".format(sorted(running_ad_group_sources)))

        current_settings_ids = list(ad_group_source_qs.values_list("settings__id", flat=True))

        duplicates_dict = defaultdict(dict)

        for e in [s for s in settings_list if s.id in current_settings_ids]:
            ad_group_id = e.ad_group_source.ad_group.id
            source_id = e.ad_group_source.source.id

            if source_id not in duplicates_dict[ad_group_id]:
                duplicates_dict[ad_group_id][source_id] = []

            duplicates_dict[ad_group_id][source_id].append(e)

        deletion_ids = []

        for ad_group_id, sources_dict in duplicates_dict.items():
            for source_id, duplicates_list in sources_dict.items():
                self.stdout.write(
                    "Summary of duplicates for AdGroup.id {} and Source.id {}\n".format(ad_group_id, source_id)
                )

                data_list = []
                for e in duplicates_list:
                    data = {
                        "id": e.id,
                        "state": e.state,
                        "ad_group_source.id": e.ad_group_source.id,
                        "ad_group_source.settings_count": e.ad_group_source.adgroupsourcesettings_set.count(),
                        "ad_group_source.repr": str(e.ad_group_source),
                        "ad_group.id": e.ad_group_source.ad_group.id,
                    }
                    data_list.append(data)
                    self.stdout.write("  - {}".format(data))

                delete_candidate_ids = set(e.id for e in duplicates_list)

                sorted_candidates = sorted(
                    data_list,
                    key=lambda x: (
                        # firstly, we prefer those settings that match running state of AdGroupSource
                        0 if x["ad_group_source.id"] in running_ad_group_sources else 1,
                        # secondly, we prefer those that have a higher number of settings
                        -x["ad_group_source.settings_count"],
                        # at the end, we prefer those that have a lower id
                        x["id"],
                    ),
                )
                delete_candidate_ids.remove(sorted_candidates[0]["id"])

                if duplicates_list and len(delete_candidate_ids) != len(duplicates_list) - 1:
                    raise ValueError("More records should be deleted: {}}".format(delete_candidate_ids))

                sorted_delete_candidate_ids = sorted(delete_candidate_ids)
                deletion_ids.extend(sorted_delete_candidate_ids)
                self.stdout.write("    -> delete: {}".format(sorted_delete_candidate_ids))

        if not dry_run and deletion_ids:
            ad_group_source_ids = list(
                models.AdGroupSource.objects.filter(settings__id__in=deletion_ids)
                .distinct()
                .values_list("id", flat=True)
            )
            all_ad_group_source_settings_ids = models.AdGroupSourceSettings.objects.filter(
                ad_group_source__id__in=ad_group_source_ids
            ).values_list("id", flat=True)

            models.AdGroupSource.objects.filter(id__in=ad_group_source_ids).update(settings=None)
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    "DELETE FROM dash_adgroupsourcesettings WHERE id IN (%s);"
                    % ", ".join([str(e) for e in all_ad_group_source_settings_ids])
                )
                deleted_settings_count = cursor.rowcount

            deleted_autopilot_logs_count, _ = automation_models.AutopilotLog.objects.filter(
                ad_group_source__id__in=ad_group_source_ids
            ).delete()
            deleted_count, _ = models.AdGroupSource.objects.filter(id__in=ad_group_source_ids).delete()
            self.stdout.write(
                "Deleted {} AdGroupSources, {} AdGroupSourceSettings and {} AutopilotLog records".format(
                    deleted_count, deleted_settings_count, deleted_autopilot_logs_count
                )
            )
