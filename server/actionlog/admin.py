from django.contrib import admin

from actionlog import models
from actionlog import constants


class ActionLogAdminAdmin(admin.ModelAdmin):
    search_fields = ('action', 'ad_group_network')
    list_filter = ('ad_group_network__network', 'state', 'action', 'action_type')

    list_display = ('action', 'ad_group_network', 'created_dt', 'action_type', 'state_')

    fields = (
        'action', 'ad_group_network', 'state_', 'action_type',
        'created_by', 'created_dt', 'modified_by', 'modified_dt',
        'message_',
    )

    readonly_fields = (
        'action', 'ad_group_network', 'state_', 'action_type',
        'created_by', 'created_dt', 'modified_by', 'modified_dt',
        'message_',
    )

    display_state_colors = {
        constants.ActionState.SUCCESS: '#5cb85c',
        constants.ActionState.FAILED: '#d9534f',
        constants.ActionState.ABORTED: '#777',
        constants.ActionState.WAITING: '#428bca',
    }

    def state_(self, obj):
        return '<span style="color:{color}">{state}</span>'.format(
            color=self.display_state_colors[obj.state],
            state=obj.get_state_display(),
        )
    state_.allow_tags = True

    def message_(self, obj):
        return '<div style="overflow: hidden"><pre style="color: #000;">{}</pre></div>'.format(obj.message)
    message_.allow_tags = True


admin.site.register(models.ActionLog, ActionLogAdminAdmin)
