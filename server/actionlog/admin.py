import json
import datetime
from urlparse import urlparse

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape

from actionlog import models
from actionlog import constants

import dash.constants


class ActionLogAdminAdmin(admin.ModelAdmin):
    class AgeFilter(admin.SimpleListFilter):
        title = 'Age'
        parameter_name = 'age'

        def lookups(self, request, model_admin):
            return [(
                '{num}d'.format(num=num),
                '{num} day{suffix}'.format(num=num, suffix='s' if num > 1 else ''))
                for num in [1, 3, 7, 30]]

        def queryset(self, request, queryset):
            days = None

            if self.value() == '1d':
                days = 1
            if self.value() == '3d':
                days = 3
            if self.value() == '7d':
                days = 7
            if self.value() == '30d':
                days = 30

            if not days:
                return

            return queryset.filter(created_dt__gte=datetime.datetime.now() - datetime.timedelta(days=days))

        def choices(self, cl):
            """ Overridden to remove default All choice """
            yield {
                'selected': self.value() is None,
                'query_string': cl.get_query_string({}, [self.parameter_name]),
            }
            for lookup, title in self.lookup_choices:
                yield {
                    'selected': self.value() == lookup,
                    'query_string': cl.get_query_string({
                        self.parameter_name: lookup,
                    }, []),
                    'display': title,
                }

    search_fields = (
        'action',
        'ad_group_source__ad_group__name',
        'ad_group_source__ad_group__campaign__name',
        'ad_group_source__ad_group__campaign__account__name',
        'ad_group_source__source__name',
    )

    list_filter = ('ad_group_source__source', 'state', 'action', 'action_type', AgeFilter)

    list_display = ('action_', 'ad_group_source_', 'created_dt', 'modified_dt', 'action_type', 'state_', 'order_')

    fields = (
        'action_', 'ad_group_source_', 'state', 'action_type',
        'created_by', 'created_dt', 'modified_by', 'modified_dt',
        'payload_', 'message_', 'order_'
    )

    readonly_fields = (
        'action_', 'ad_group_source_', 'action_type',
        'created_by', 'created_dt', 'modified_by', 'modified_dt',
        'payload_', 'message_', 'order_'
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
    state_.admin_order_field = 'state'

    def message_(self, obj):
        return self._wrap_preformatted_text(obj.message)
    message_.allow_tags = True

    def order_(self, obj):
        if obj.order is not None:
            return obj.order.id
        else:
            return 'n/a'
    order_.admin_order_field = 'order'
    order_.short_description = 'Order ID'

    def ad_group_source_(self, obj):
        return '<a href="{ad_group_url}">{ad_group}</a>: <a href="{source_url}">{source}</a>'.format(
            ad_group_url=reverse('admin:dash_adgroup_change', args=(obj.ad_group_source.ad_group.id,)),
            ad_group=obj.ad_group_source.ad_group,
            source_url=reverse('admin:dash_source_change', args=(obj.ad_group_source.source.id,)),
            source=obj.ad_group_source.source,
        )
    ad_group_source_.allow_tags = True
    ad_group_source_.admin_order_field = 'ad_group_source'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_actions(self, request):
        actions = super(ActionLogAdminAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def action_(self, obj):
        if obj.action == constants.Action.FETCH_REPORTS:
            description = 'for {}'.format(
                obj.payload and obj.payload.get('args', {}).get('date') or '\(O_o)/',
            )
        elif obj.action == constants.Action.SET_PROPERTY:
            prop = obj.payload and obj.payload.get('property')
            value = obj.payload and obj.payload.get('value')

            if prop == 'state':
                value = dash.constants.AdGroupSourceSettingsState.get_text(value)
            elif isinstance(value, list):
                value = ', '.join(value)

            description = '{} to {}'.format(
                prop or '\(O_o)/',
                value or '\(O_o)/'
            )
        elif obj.action == constants.Action.SET_CAMPAIGN_STATE:
            state = dash.constants.AdGroupSettingsState.get_text(
                obj.payload.get('args', {}).get('state')
            )

            description = 'to {}'.format(state or '\(O_o)/')
        else:
            return obj.action

        return '{action} <span style="color: #999;">{description}</span>'.format(
            action=obj.action,
            description=description,
        )
    action_.allow_tags = True
    action_.admin_order_field = 'action'

    def payload_(self, obj):
        return self._wrap_preformatted_text(json.dumps(obj.payload, indent=4))
    payload_.allow_tags = True

    def _wrap_preformatted_text(self, text):
        return '<div style="overflow: hidden;"><pre style="color: #000;">{}</pre></div>'.format(escape(text))

    def changelist_view(self, request, extra_context=None):
        if 'age' not in request.GET:
            q = request.GET.copy()
            q['age'] = '1d'  # default value
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()

        return super(ActionLogAdminAdmin, self).changelist_view(
                request, extra_context=extra_context)


admin.site.register(models.ActionLog, ActionLogAdminAdmin)
