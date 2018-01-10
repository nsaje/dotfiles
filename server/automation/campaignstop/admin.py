import pprint
import textwrap

from django.contrib import admin

from . import constants
from .service.update_campaignstop_state import THRESHOLD


class RealTimeCampaignStopLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'event', 'event_result', 'created_dt')
    readonly_fields = ('created_dt', 'event_result', 'event_description')
    exclude = ('context',)

    def event_description(self, obj):
        if not obj.context:
            return 'No context captured.'

        if obj.event == constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK:
            return self._get_depletion_check_description(obj)
        elif obj.event == constants.CampaignStopEvent.SELECTION_CHECK:
            pass
        elif obj.event == constants.CampaignStopEvent.MAX_ALLOWED_END_DATE_UPDATE:
            return self._get_max_allowed_end_date_update_description(obj)
        elif obj.event == constants.CampaignStopEvent.BUDGET_AMOUNT_VALIDATION:
            pass
        return 'Event type unknown. Captured context:\n{}'.format(pprint.pformat(obj.context))
    event_description.allow_tags = True

    def _get_depletion_check_description(self, obj):
        desc = textwrap.dedent('''\
            The calculated campaign state is: {state}.

            Max allowed end date: {max_allowed_end_date} (is in past: {is_max_end_date_past})
            Available budget (until above date): ${budget_spends_until_date}''')
        if 'budget_spends_until_date' in obj.context:
            desc += textwrap.dedent('''
                Spend from daily statements was taken until <b>{budget_spends_until_date}</b>. Real time data was used for dates after that.
                Spend data taken into account:
                    - Real time spend (current): ${current_rt_spend}
                    - Real time spend (previous check): ${prev_rt_spend}
                    - Spend rate: ${spend_rate}
                    - Prediction for next check: ${predicted}
                    - Is below threshold (${threshold}): {is_below_threshold}''')
        return desc.format(state=self._format_state(obj), threshold=THRESHOLD, **obj.context)

    def _get_max_allowed_end_date_update_description(self, obj):
        desc = 'Calculated maximum allowed campaign end date: {max_allowed_end_date}'.format(**obj.context)
        desc += 'Campaign budgets taken into account:'
        for budget in obj.context['budgets']:
            desc += '\n    - id: {id}, start: {start_date}, end: {end_date}'.format(**budget)
        return desc

    def event_result(self, obj):
        if obj.event == constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK:
            return self._format_state(obj)
        elif obj.event == constants.CampaignStopEvent.SELECTION_CHECK:
            pass
        elif obj.event == constants.CampaignStopEvent.MAX_ALLOWED_END_DATE_UPDATE:
            return obj.context['max_allowed_end_date'].isoformat()
        elif obj.event == constants.CampaignStopEvent.BUDGET_AMOUNT_VALIDATION:
            pass
        return 'N/A'
    event_result.allow_tags = True

    @staticmethod
    def _format_state(obj):
        state = constants.CampaignStopState.STOPPED
        if obj.context['allowed_to_run']:
            state = constants.CampaignStopState.ACTIVE
        return '<div style="color:{color}"><b>{state_text}</b></div>'.format(
            color='green' if state == constants.CampaignStopState.ACTIVE else 'red',
            state_text=constants.CampaignStopState.get_text(state),
        )
