from django.contrib import admin

from dcron.models import DCronJob
from dcron.models import DCronJobSettings


@admin.register(DCronJob)
class DCronJobAdmin(admin.ModelAdmin):
    ordering = ["command_name"]
    list_display = ("command_name", "host", "duration", "executed_dt", "completed_dt", "alert")
    search_fields = ("command_name",)
    list_filter = ("alert", "dcronjobsettings__enabled", "dcronjobsettings__manual_override")

    def duration(self, obj):
        if obj.executed_dt and obj.completed_dt:
            return obj.completed_dt - obj.executed_dt

        return "-"

    duration.short_description = "Duration"


@admin.register(DCronJobSettings)
class DCronJobAdminSettings(admin.ModelAdmin):
    ordering = ["job__command_name"]
    raw_id_fields = ("job",)
    list_display = ("job", "schedule", "full_command", "enabled", "warning_wait", "max_duration", "manual_override")
    search_fields = ("job__command_name",)
    list_filter = ("job__alert", "enabled", "manual_override")
