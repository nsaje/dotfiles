import datetime

from django.template.loader import render_to_string

import dash.models
import dash.constants
import analytics.projections
from utils import converters
from utils.html_helpers import TableCell, TableRow, Url

NEW_ITEMS_LIST_REPORT_TITLES = {
    'campaigns': 'Campaigns created yesterday',
    'accounts': 'Accounts created yesterday',
    'credits': 'Yesterday\'s credit items',
    'budgets': 'Yesterday\'s budget items',
}

CHANGED_ITEMS_LIST_REPORT_TITLES = {
    'credits': 'Credit line items updated yesterday',
    'budgets': 'Budget line items updated yesterday',
}


LIST_REPORT_DISPLAY = {
    'campaigns': lambda obj: Url(
        _url(['v2', 'analytics', 'campaign', obj.pk]),
        obj.get_long_name()
    ).as_html(),
    'accounts': lambda obj: Url(
        _url(['v2', 'analytics', 'account', obj.pk]),
        obj.get_long_name()
    ).as_html(),
    'credits': lambda obj: '{} ({})'.format(
        Url(
            obj.account and _url(['v2', 'analytics', 'account', obj.account_id]) or
            obj.agency and _url(['v2', 'analytics', 'account', obj.agency.account_set.all().first().pk]) or
            '#',
            str(obj)
        ).as_html(), _get_bcm_changes('credit', obj)
    ),
    'budgets': lambda obj: '{} ({})'.format(Url(
        _url(['v2', 'analytics', 'campaign', obj.campaign_id]),
        '{}, {}'.format(str(obj), obj.campaign.account.get_long_name())
    ).as_html(), _get_bcm_changes('budget', obj)),
}

OEN_ACCOUNTS = (305, )
OEN_AGENCIES = (55, )


def _format_change(key, change):
    if '_nano' in key:
        return list(map(converters.nano_to_decimal, change))
    if '_cc' in key:
        return list(map(converters.cc_to_decimal, change))
    return change


def _get_dict_change(d_prev, d_after):
    return {
        k: (d_prev.get(k), d_after[k], ) for k in d_after if d_after[k] != d_prev.get(k)
    }


def _get_bcm_changes(name, obj):
    history = obj.history.all().order_by('-created_dt')[:2]
    if len(history) < 2:
        return ''
    changes = _get_dict_change(history[1].snapshot, history[0].snapshot)
    return ', '.join([
        '{}: {} -> {}'.format(key, *_format_change(key, chng))
        for key, chng in changes.items()
    ])


class ReportContext(object):

    def __init__(self, date):
        self.date = date
        self.date_after = date + datetime.timedelta(1)

        self._prepare_main_model()

        self.agencies = self._get_subset_model(lambda s: s.budget.campaign.account.agency_id)
        self.accounts = self._get_subset_model(lambda s: s.budget.campaign.account_id)
        self.campaigns = self._get_subset_model(lambda s: s.budget.campaign_id)

        self.agency_accounts = set(
            acc.pk for acc in dash.models.Account.objects.filter(agency_id__isnull=False).exclude(agency_id__in=OEN_AGENCIES)
        )
        self.agency_campaigns = set(
            camp.pk for camp in dash.models.Campaign.objects.filter(account__agency_id__isnull=False).exclude(account__agency_id__in=OEN_AGENCIES)
        )

        self.account_types = {
            sett.account_id: sett.account_type
            for sett in dash.models.AccountSettings.objects.exclude(
                account_id__in=OEN_ACCOUNTS
            ).group_current_settings()
        }
        self.campaign_types = {
            c.pk: self.account_types.get(c.account_id, dash.constants.AccountType.UNKNOWN)
            for c in dash.models.Campaign.objects.exclude(account_id__in=OEN_ACCOUNTS)
        }

        yesterday_range = {
            'created_dt__lt': self.date_after,
            'created_dt__gte': self.date,
        }
        self.yesterday_created = {
            'accounts': dash.models.Account.objects.filter(**yesterday_range).exclude(pk__in=OEN_ACCOUNTS),
            'campaigns': dash.models.Campaign.objects.filter(**yesterday_range).exclude(account_id__in=OEN_ACCOUNTS),
            'budgets': dash.models.BudgetLineItem.objects.filter(**yesterday_range).exclude(campaign__account_id__in=OEN_ACCOUNTS),
            'credits': dash.models.CreditLineItem.objects.filter(**yesterday_range).exclude(
                account_id__in=OEN_ACCOUNTS
            ).exclude(agency_id__in=OEN_AGENCIES),
        }

        yesterday_range = {
            'modified_dt__lt': self.date_after,
            'modified_dt__gte': self.date,
        }
        self.yesterday_modified = {
            'budgets': dash.models.BudgetLineItem.objects.filter(**yesterday_range).exclude(campaign__account_id__in=OEN_ACCOUNTS),
            'credits': dash.models.CreditLineItem.objects.filter(**yesterday_range).exclude(
                account_id__in=OEN_ACCOUNTS
            ).exclude(agency_id__in=OEN_AGENCIES),
        }

    def _get_data_model(self):
        return {
            'this_day': set(),
            'prev_day': set(),

            'this_week': set(),
            'prev_week': set(),

            'this_month': set(),
            'prev_month': set(),
        }

    def _filter_statements(self, fun, statements):
        mapped_statements = list(map(fun, statements))
        nonnill_statements = list(filter(bool, mapped_statements))
        return nonnill_statements

    def _get_subset_model(self, fun_get_id):
        return {
            time_span: set(self._filter_statements(fun_get_id, statements))
            for time_span, statements in self.statements.items()
        }

    def _prepare_main_model(self):
        start_month = self.date.month - 1
        start_date = datetime.date(
            self.date.year if start_month > 0 else self.date.year - 1,
            12 if start_month < 1 else start_month,
            1
        )

        statements_qs = dash.models.BudgetDailyStatement.objects.filter(
            date__gte=start_date,
            date__lte=self.date,
        ).select_related('budget__campaign').select_related('budget__campaign__account')

        curr_week = self.date.isocalendar()[1]
        prev_week = (self.date - datetime.timedelta(7)).isocalendar()[1]
        day_before = self.date - datetime.timedelta(1)

        self.statements = self._get_data_model()
        for s in statements_qs:
            week = s.date.isocalendar()[1]

            if s.date.day == self.date:
                self.statements['this_day'].add(s)
            elif s.date.day == day_before:
                self.statements['prev_day'].add(s)

            if week == curr_week:
                self.statements['this_week'].add(s)
            elif week == prev_week:
                self.statements['prev_week'].add(s)

            if s.date.month == self.date.month:
                self.statements['this_month'].add(s)
            else:
                self.statements['prev_month'].add(s)


def _url(path):
    return 'https://one.zemanta.com/' + '/'.join(str(p) for p in path)


def _get_totals(table, col):
    return TableCell(sum(row[col].value for row in table))


def _get_change(span, obj, subset):
    curr = obj['this_' + span] & subset
    prev = obj['prev_' + span] & subset
    return len(curr) - len(prev)


def _get_counts(obj, subset=None, total_only=False):
    if subset is None:
        # If no subset is specified, everything should be valid: intersect with all objects
        subset = obj['this_month'] | obj['prev_month']
    cell = TableCell(len(obj['this_month'] & subset), info=[
        _get_change('day', obj, subset),
        _get_change('week', obj, subset),
        _get_change('month', obj, subset)
    ] if not total_only else [])
    return cell


def _get_oen(context):
    oen_campaigns = set(dash.models.Campaign.objects.filter(account_id__in=OEN_ACCOUNTS).values_list('pk', flat=True))
    projections = analytics.projections.CurrentMonthBudgetProjections(
        'account',
        accounts=dash.models.Account.objects.filter(pk__in=OEN_ACCOUNTS),
        campaign_id__in=oen_campaigns
    )
    return [
        TableCell(1),
        _get_counts(context.campaigns, oen_campaigns),
        TableCell(projections.total('attributed_media_spend')),
        TableCell(projections.total('allocated_media_budget')),
        TableCell(projections.total('media_spend_projection')),
        TableCell(projections.total('total_fee_projection')),
    ]


def _populate_agency(context, type_filter):
    valid_accounts = set(
        account_id
        for account_id, account_type in context.account_types.items()
        if account_type == type_filter
    ) & context.agency_accounts
    valid_campaigns = set(
        campaign_id
        for campaign_id, campaign_type in context.campaign_types.items()
        if campaign_type == type_filter
    ) & context.agency_campaigns

    monthly_campaigns = context.campaigns['this_month'] & valid_campaigns
    projections = analytics.projections.CurrentMonthBudgetProjections(
        'account',
        accounts=dash.models.Account.objects.filter(pk__in=valid_accounts),
        campaign_id__in=monthly_campaigns
    )
    postfix = ""
    if type_filter not in analytics.projections.BudgetProjections.MANAGED_ACCOUNT_TYPES:
        postfix = " *"
    return [
        _get_counts(context.accounts, valid_accounts),
        _get_counts(context.campaigns, valid_campaigns),
        TableCell(projections.total('attributed_media_spend')),
        TableCell(projections.total('allocated_media_budget')),
        TableCell(projections.total('media_spend_projection'), postfix=postfix),
        TableCell(projections.total('total_fee_projection'), postfix=postfix),
    ]


def _populate_clientdirect(context, type_filter):
    valid_accounts = set(
        account_id
        for account_id, account_type in context.account_types.items()
        if account_type == type_filter
    ) - context.agency_accounts
    valid_campaigns = set(
        campaign_id
        for campaign_id, campaign_type in context.campaign_types.items()
        if campaign_type == type_filter
    ) - context.agency_campaigns

    monthly_campaigns = context.campaigns['this_month'] & valid_campaigns
    projections = analytics.projections.CurrentMonthBudgetProjections(
        'account',
        accounts=dash.models.Account.objects.filter(pk__in=valid_accounts),
        campaign_id__in=monthly_campaigns
    )
    postfix = ""
    if type_filter not in analytics.projections.BudgetProjections.MANAGED_ACCOUNT_TYPES:
        postfix = " *"
    return [
        _get_counts(context.accounts, valid_accounts),
        _get_counts(context.campaigns, valid_campaigns),
        TableCell(projections.total('attributed_media_spend')),
        TableCell(projections.total('allocated_media_budget')),
        TableCell(projections.total('media_spend_projection'), postfix=postfix),
        TableCell(projections.total('total_fee_projection'), postfix=postfix),
    ]


def _prepare_table_rows(context):
    header = [TableRow(list(map(TableCell, [
        context.date.strftime('%B %d'),
        '# active accounts<br />(d/d, w/w, m/m)',
        '# active campaigns<br />(d/d, w/w, m/m)',
        'media spend MTD',
        'monthly budgets',
        'spend projection',
        'fee projection'
    ])))]
    agency_rows = list(map(TableRow.prepare(TableRow.TYPE_BREAKDOWN), [
        [TableCell('Managed', align='right')] + _populate_agency(context, dash.constants.AccountType.MANAGED),
        [TableCell('PAAS', align='right')] + _populate_agency(context, dash.constants.AccountType.PAAS),
        [TableCell('Pilot', align='right')] + _populate_agency(context, dash.constants.AccountType.PILOT),
        [TableCell('Activated', align='right')] + _populate_agency(context, dash.constants.AccountType.ACTIVATED),
        [TableCell('Test', align='right')] + _populate_agency(context, dash.constants.AccountType.TEST),
        [TableCell('Unknown', align='right')] + _populate_agency(context, dash.constants.AccountType.UNKNOWN),
    ]))
    agency_costs = [TableRow([
        TableCell('{} agencies'.format(
            _get_counts(context.agencies, total_only=True).value_html()
        )),
        _get_counts(context.accounts, context.agency_accounts, total_only=True),
        _get_counts(context.campaigns, context.agency_campaigns, total_only=True),
    ] + [
        _get_totals(agency_rows, i) for i in range(3, 7)
    ], row_type=TableRow.TYPE_TOTALS)]

    clientdirect_rows = list(map(TableRow.prepare(TableRow.TYPE_BREAKDOWN), [
        [TableCell('Managed', align='right')] + _populate_clientdirect(context, dash.constants.AccountType.MANAGED),
        [TableCell('PAAS', align='right')] + _populate_clientdirect(context, dash.constants.AccountType.PAAS),
        [TableCell('Pilot', align='right')] + _populate_clientdirect(context, dash.constants.AccountType.PILOT),
        [TableCell('Activated', align='right')] +
        _populate_clientdirect(context, dash.constants.AccountType.ACTIVATED),
        [TableCell('Test', align='right')] + _populate_clientdirect(context, dash.constants.AccountType.TEST),
        [TableCell('Unknown', align='right')] + _populate_clientdirect(context, dash.constants.AccountType.UNKNOWN),
    ]))
    clientdirect_totals = [TableRow([TableCell('Client-direct')] + [
        _get_totals(clientdirect_rows, i) for i in range(1, 7)
    ], row_type=TableRow.TYPE_TOTALS)]

    grand_totals = [
        TableRow([TableCell('Z1 Total')] + [
            _get_totals(agency_costs + clientdirect_totals, i) for i in range(1, 7)
        ], row_type=TableRow.TYPE_TOTALS),
        TableRow([TableCell('OEN Total')] + _get_oen(context), row_type=TableRow.TYPE_TOTALS)
    ]

    return header + agency_costs + agency_rows + clientdirect_totals \
        + clientdirect_rows + grand_totals


def _generate_table_html(context):
    html = '<table style="width:100%" cellspacing="5px" cellpading="2px"><caption>Daily Management Report</caption>'
    for position, row in enumerate(_prepare_table_rows(context)):
        html += row.as_html(position)
    html += '</table>'
    return html


def _generate_lists_html(context):
    data = []
    for item, elements in context.yesterday_created.items():
        data.append({
            'title': NEW_ITEMS_LIST_REPORT_TITLES[item],
            'elements': [
                LIST_REPORT_DISPLAY[item](elt) for elt in elements
            ]
        })

    for item, elements in context.yesterday_modified.items():
        data.append({
            'title': CHANGED_ITEMS_LIST_REPORT_TITLES[item],
            'elements': [
                LIST_REPORT_DISPLAY[item](elt) for elt in elements
            ]
        })
    return data


def get_daily_report_html(date=None):
    if not date:
        date = datetime.date.today() - datetime.timedelta(1)

    context = ReportContext(date)
    return render_to_string('management_report.html', {
        'table': _generate_table_html(context),
        'lists': _generate_lists_html(context),
    })
