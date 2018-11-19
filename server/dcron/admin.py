from django.contrib import admin

from dcron import models


@admin.register(models.DCronJob)
class DCronJobAdmin(admin.ModelAdmin):
    ordering = ["command_name"]
    list_display = ("command_name", "host", "duration", "executed_dt", "completed_dt", "alert")
    search_fields = ("command_name",)
    list_filter = (
        "alert",
        "dcronjobsettings__enabled",
        "dcronjobsettings__severity",
        "dcronjobsettings__manual_override",
    )
    readonly_fields = ("command_name", "host", "executed_dt", "completed_dt", "alert")

    def duration(self, obj):
        if obj.executed_dt and obj.completed_dt:
            return obj.completed_dt - obj.executed_dt

        return "-"

    duration.short_description = "Duration"


@admin.register(models.DCronJobSettings)
class DCronJobAdminSettings(admin.ModelAdmin):
    ordering = ["job__command_name"]
    raw_id_fields = ("job",)
    list_display = (
        "job",
        "schedule",
        "full_command",
        "enabled",
        "severity",
        "warning_wait",
        "max_duration",
        "min_separation",
        "manual_override",
    )
    search_fields = ("job__command_name",)
    list_filter = ("job__alert", "enabled", "severity", "manual_override")
    readonly_fields = ("job", "schedule", "full_command", "enabled")
