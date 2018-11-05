from django.contrib import admin

from dcron.models import DCronJob, DCronJobSettings


@admin.register(DCronJob)
class DCronJobAdmin(admin.ModelAdmin):
    ordering = ["command_name"]
    list_display = ("command_name", "host", "duration", "executed_dt", "completed_dt")
    search_fields = ("command_name",)
    list_filter = ("dcronjobsettings__enabled", "dcronjobsettings__manual_warning_wait")

    def duration(self, obj):
        if obj.executed_dt and obj.completed_dt:
            return obj.completed_dt - obj.executed_dt

        return "-"

    duration.short_description = "Duration"


@admin.register(DCronJobSettings)
class DCronJobAdminSettings(admin.ModelAdmin):
    ordering = ["job__command_name"]
    raw_id_fields = ("job",)
    list_display = ("job", "schedule", "full_command", "enabled", "warning_wait", "manual_warning_wait")
    search_fields = ("job__command_name",)
    list_filter = ("enabled", "manual_warning_wait")
