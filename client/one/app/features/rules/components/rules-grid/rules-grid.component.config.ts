import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {Rule} from '../../../../core/rules/types/rule';
import {RuleActionConfig} from '../../../../core/rules/types/rule-action-config';
import {
    RULE_ACTION_FREQUENCY_OPTIONS,
    RULE_ACTION_TYPES_OPTIONS,
    RULE_NOTIFICATION_OPTIONS,
    RULE_TARGET_TYPES,
} from '../../rules.config';
import {
    RuleNotificationType,
    RuleActionType,
    RuleState,
    RuleActionFrequency,
} from '../../../../core/rules/rules.constants';
import {RuleActionsCellComponent} from '../rule-actions-cell/rule-actions-cell.component';
import {SwitchButtonCellComponent} from '../../../../shared/components/smart-grid/components/cells/switch-button-cell/switch-button-cell.component';
import {SwitchButtonRendererParams} from '../../../../shared/components/smart-grid/components/cells/switch-button-cell/types/switch-button.renderer-params';
import {RuleRunsOnCellComponent} from '../rule-runs-on-cell/rule-runs-on-cell.component';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RuleEntity} from '../../../../core/rules/types/rule-entity';
import {RuleEntities} from '../../../../core/rules/types/rule-entities';
import {MappedRuleEntity} from '../../types/mapped-rule-entity';
import {ViewportBreakpoint} from '../../../../app.constants';

export const COLUMN_NAME: SmartGridColDef = {
    headerName: 'Name',
    field: 'name',
    width: 120,
    resizable: true,
    suppressSizeToFit: true,
};

export const COLUMN_ACTION: SmartGridColDef = {
    headerName: 'Action',
    width: 160,
    suppressSizeToFit: true,
    valueGetter: actionGetter,
};

export const COLUMN_STATUS: SmartGridColDef = {
    headerName: 'Status',
    field: 'state',
    width: 60,
    suppressSizeToFit: true,
    cellRendererFramework: SwitchButtonCellComponent,
    cellRendererParams: {
        isSwitchedOn: (params: SwitchButtonRendererParams) => {
            return params.data.state === RuleState.ENABLED;
        },
        isDisabled: (params: SwitchButtonRendererParams) => {
            return params.context.componentParent.store.isReadOnly(params.data);
        },
        toggle: (value: boolean, params: SwitchButtonRendererParams) => {
            params.context.componentParent.onRuleStateToggle(
                params.data,
                value
            );
        },
    } as SwitchButtonRendererParams,
};

export const COLUMN_ACTION_FREQUENCY: SmartGridColDef = {
    headerName: 'Action frequency',
    field: 'actionFrequency',
    width: 120,
    resizable: true,
    suppressSizeToFit: true,
    valueFormatter: actionFrequencyFormatter,
};

export const COLUMN_NOTIFICATION: SmartGridColDef = {
    headerName: 'Notification',
    field: 'notificationType',
    width: 140,
    resizable: true,
    suppressSizeToFit: true,
    valueFormatter: notificationTypeFormatter,
};

export const COLUMN_RUNS_ON: SmartGridColDef = {
    headerName: 'Runs on',
    field: 'entities',
    width: 200,
    suppressSizeToFit: true,
    resizable: true,
    cellRendererFramework: RuleRunsOnCellComponent,
    cellRendererParams: {
        getEntities: (rule: Rule) => getMappedEntities(rule.entities),
    },
};

export const COLUMN_RUNS_ON_TOOLTIP: SmartGridColDef = {
    headerName: '',
    maxWidth: 80,
    minWidth: 80,
    resizable: true,
    valueGetter: runsOnGetter,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Comment,
            placement: 'left',
        },
    } as IconTooltipRendererParams<string, Rule, any>,
};

export const COLUMN_SCOPE: SmartGridColDef = {
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
    valueGetter: params => {
        return {
            agencyId: params.data.agencyId,
            accountId: params.data.accountId,
        };
    },
};

export const COLUMN_ACTIONS: SmartGridColDef = {
    headerName: '',
    cellRendererFramework: RuleActionsCellComponent,
    pinned: 'right',
    width: 75,
    suppressSizeToFit: true,
    resizable: true,
    unpinBelowGridWidth: ViewportBreakpoint.Tablet,
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

function actionGetter(params: {data: Rule}): string {
    const targetType = RULE_TARGET_TYPES.find(
        targetType => targetType.value === params.data.targetType
    );
    return (
        targetType.availableActions.find(
            targetAction => targetAction.type === params.data.actionType
        ).label || 'N/A'
    );
}

function runsOnGetter(params: {data: Rule}): string {
    return getMappedEntities(params.data.entities)
        .map(entity => `${entity.type} (${entity.name})`)
        .join(', ');
}

function getMappedEntities(entities: RuleEntities): MappedRuleEntity[] {
    const mappedEntities = [];
    mappedEntities.push(
        ...mapEntities(entities.accounts?.included || [], 'Account', 'account')
    );
    mappedEntities.push(
        ...mapEntities(
            entities.campaigns?.included || [],
            'Campaign',
            'campaign'
        )
    );
    mappedEntities.push(
        ...mapEntities(entities.adGroups?.included || [], 'Ad Group', 'adgroup')
    );
    return mappedEntities;
}

function mapEntities(
    entities: RuleEntity[],
    entityTypeName: string,
    entityTypeUrl: string
): MappedRuleEntity[] {
    return entities.map(entity => {
        return {
            type: entityTypeName,
            name: entity.name,
            link: `/v2/analytics/${entityTypeUrl}/${entity.id}`,
        };
    });
}
