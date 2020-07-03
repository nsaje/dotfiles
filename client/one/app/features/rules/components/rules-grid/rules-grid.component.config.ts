import {ColDef} from 'ag-grid-community';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/types/item-scope.renderer-params';
import {Rule} from '../../../../core/rules/types/rule';
import {
    RULE_ACTION_FREQUENCY_OPTIONS,
    RULE_ACTIONS_OPTIONS,
    RULE_STATE_OPTIONS,
    RULE_NOTIFICATION_OPTIONS,
} from '../../rules.config';
import {
    RuleNotificationType,
    RuleActionType,
    RuleState,
    RuleActionFrequency,
} from '../../../../core/rules/rules.constants';

export const COLUMN_NAME: ColDef = {
    headerName: 'Name',
    field: 'name',
    width: 80,
    resizable: false,
    suppressSizeToFit: true,
};

export const COLUMN_ACTION_TYPE: ColDef = {
    headerName: 'Action type',
    field: 'actionType',
    width: 150,
    suppressSizeToFit: true,
    valueFormatter: actionTypeFormatter,
};

export const COLUMN_STATUS: ColDef = {
    headerName: 'Status',
    field: 'state',
    width: 80,
    resizable: false,
    suppressSizeToFit: true,
    valueFormatter: ruleStateFormatter,
};

export const COLUMN_ACTION_FREQUENCY: ColDef = {
    headerName: 'Action frequency',
    field: 'actionFrequency',
    width: 110,
    resizable: false,
    suppressSizeToFit: true,
    valueFormatter: actionFrequencyFormatter,
};

export const COLUMN_NOTIFICATION: ColDef = {
    headerName: 'Notification',
    field: 'notificationType',
    width: 80,
    resizable: false,
    suppressSizeToFit: true,
    valueFormatter: notificationTypeFormatter,
};

export const COLUMN_SCOPE: ColDef = {
    headerName: 'Scope',
    minWidth: 200,
    resizable: true,
    cellRendererFramework: ItemScopeCellComponent,
    cellRendererParams: {
        getAgencyLink: item => {
            return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
        },
        getAccountLink: item => {
            return `/v2/analytics/account/${item.accountId}`;
        },
    } as ItemScopeRendererParams<Rule>,
};

function notificationTypeFormatter(params: {
    value: RuleNotificationType;
}): string {
    return RULE_NOTIFICATION_OPTIONS[params.value]?.label || 'N/A';
}

function actionFrequencyFormatter(params: {
    value: RuleActionFrequency;
}): string {
    return RULE_ACTION_FREQUENCY_OPTIONS[params.value]?.label || 'N/A';
}

function actionTypeFormatter(params: {value: RuleActionType}): string {
    return RULE_ACTIONS_OPTIONS[params.value]?.label || 'N/A';
}

function ruleStateFormatter(params: {value: RuleState}): string {
    return RULE_STATE_OPTIONS[params.value]?.label || 'N/A';
}
