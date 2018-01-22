import pprint
import textwrap

from django.contrib import admin

from . import constants


class RealTimeCampaignStopLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'event', 'event_result', 'created_dt')
    list_filter = ('event',)
    readonly_fields = ('event', 'created_dt', 'event_result', 'event_description')
    raw_id_fields = ('campaign',)
    exclude = ('context',)
    search_fields = (
        'campaign__account__agency__id',
        'campaign__account__agency__name',
        'campaign__account__name',
        'campaign__account__id',
        'campaign__name',
        'campaign__id',
    )

    def event_description(self, obj):
        if not obj.context:
            return 'No context captured.'

        if obj.event == constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK:
            return self._get_depletion_check_description(obj)
        elif obj.event == constants.CampaignStopEvent.SELECTION_CHECK:
            return self._get_almost_depleted_budget_description(obj)
        elif obj.event == constants.CampaignStopEvent.MAX_ALLOWED_END_DATE_UPDATE:
            return self._get_max_allowed_end_date_update_description(obj)
        elif obj.event == constants.CampaignStopEvent.BUDGET_AMOUNT_VALIDATION:
            pass
        return 'Event type unknown. Captured context:\n{}'.format(pprint.pformat(obj.context))
    event_description.allow_tags = True

    def _get_depletion_check_description(self, obj):
        desc = textwrap.dedent('''\
            The calculated campaign state is: {state}

            Max allowed end date: <b>{max_allowed_end_date}</b> (is in past: {is_max_end_date_past})''')
        curr_spends = 'n/a'
        prev_spends = 'n/a'
        if 'budget_spends_until_date' in obj.context:
            if 'current_rt_spends_per_date' in obj.context:
                curr_spends = ', '.join('{}: ${}'.format(*el) for el in obj.context['current_rt_spends_per_date'])
            if 'prev_rt_spends_per_date' in obj.context:
                prev_spends = ', '.join('{}: ${}'.format(*el) for el in obj.context['prev_rt_spends_per_date'])
            desc += textwrap.dedent('''
                Prediction for next check: <b>${predicted}</b> (= ${available_budget} (available budget) - ${current_rt_spend} (real time spend) - ${spend_rate} (spend rate)) <b>{threshold_op} ${threshold}</b> (threshold)

                Spend from daily statements was taken until {budget_spends_until_date}. Real time data was used for dates after that.
                Available budget (up until {budget_spends_until_date}): ${available_budget}

                Real time data break down:
                &nbsp;&nbsp;&nbsp;&nbsp;- Real time spend (current check): ${current_rt_spend}; per date - {curr_spends}
                &nbsp;&nbsp;&nbsp;&nbsp;- Real time spend (previous check): ${prev_rt_spend}; per date - {prev_spends}
                &nbsp;&nbsp;&nbsp;&nbsp;- Spend rate: ${spend_rate} (= ${current_rt_spend} (current) - ${prev_rt_spend} (previous))''')
        return desc.format(
            state=self._format_state(obj),
            threshold=obj.context.pop('threshold', '10'),  # old default
            curr_spends=curr_spends,
            prev_spends=prev_spends,
            threshold_op='<' if obj.context.get('is_below_threshold') else '>',
            **obj.context
        ).replace('\n', '<br />')

    def _get_max_allowed_end_date_update_description(self, obj):
        desc = 'Calculated maximum allowed campaign end date: <b>{}</b>'.format(
            self._format_max_allowed_end_date(obj))
        desc += '\n\nCampaign budgets taken into account:'
        for budget in obj.context['budgets']:
            desc += '\n&nbsp;&nbsp;&nbsp;&nbsp;- id: {id}, start date: {start_date}, end date: {end_date}'.format(**budget)
        return desc.replace('\n', '<br />')

    def _get_almost_depleted_budget_description(self, obj):
        desc = textwrap.dedent('''\
            <div style="width: 280px"><pre>
            <div>Min remaining budget: <span style="font-size:1.2em; float: right">{min_remaining_budget}</span></div>
            <div>Campaign daily budget: <span style="font-size:1.2em; float: right">{campaign_daily_budget}</span></div>
            <div>Remaining current budget: <span style="font-size:1.2em; float: right">{remaining_current_budget}</span></div>
            </pre></div>
            <hr>

            <strong>Formula</strong>:
            min remaining budget = remaining current budget - campaign daily budget

            <strong>Description</strong>:
            "Min remaining budget" tells us what would happen if we do not stop the spending today.
            "Campaign daily budget" is campaign daily cap.
            "Remaining current budget" is campaign\'s available amount.''')

        return desc.format(
            min_remaining_budget=obj.context['min_remaining_budget'],
            campaign_daily_budget=obj.context['campaign_daily_budget'],
            remaining_current_budget=obj.context['remaining_current_budget'],
        ).replace('\n', '<br />')

    def event_result(self, obj):
        if obj.event == constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK:
            return self._format_state(obj)
        elif obj.event == constants.CampaignStopEvent.SELECTION_CHECK:
            return self._format_almost_depleted(obj)
        elif obj.event == constants.CampaignStopEvent.MAX_ALLOWED_END_DATE_UPDATE:
            return self._format_max_allowed_end_date(obj)
        elif obj.event == constants.CampaignStopEvent.BUDGET_AMOUNT_VALIDATION:
            pass
        return 'N/A'
    event_result.allow_tags = True

    @staticmethod
    def _format_state(obj):
        state = constants.CampaignStopState.STOPPED
        if obj.context['allowed_to_run']:
            state = constants.CampaignStopState.ACTIVE
        return '<span style="color:{color}"><b>{state_text}</b></span>'.format(
            color='#4bb543' if state == constants.CampaignStopState.ACTIVE else '#ba2121',
            state_text=constants.CampaignStopState.get_text(state),
        )

    @staticmethod
    def _format_max_allowed_end_date(obj):
        return '<b>' + obj.context['max_allowed_end_date'] + '</b>'

    @staticmethod
    def _format_almost_depleted(obj):
        return "<b>{}</b>".format(obj.context.get('is_almost_depleted'))
