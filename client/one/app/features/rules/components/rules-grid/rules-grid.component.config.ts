import {ColDef} from 'ag-grid-community';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/types/item-scope.renderer-params';
import {Rule} from '../../../../core/rules/types/rule';
import {RuleActionConfig} from '../../../../core/rules/types/rule-action-config';
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
import {RuleActionsCellComponent} from '../rule-actions-cell/rule-actions-cell.component';
import {SwitchButtonCellComponent} from '../../../../shared/components/smart-grid/components/cell/switch-button-cell/switch-button-cell.component';
import {SwitchButtonRendererParams} from '../../../../shared/components/smart-grid/components/cell/switch-button-cell/types/switch-button.renderer-params';
import {RulesView} from '../../views/rules/rules.view';
import {RuleRunsOnCellComponent} from '../rule-runs-on-cell/rule-runs-on-cell.component';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RuleEntity} from '../../../../core/rules/types/rule-entity';
import {RuleEntities} from '../../../../core/rules/types/rule-entities';
import {MappedRuleEntity} from '../../types/mapped-rule-entity';

export const COLUMN_NAME: ColDef = {
    headerName: 'Name',
    field: 'name',
    width: 120,
    resizable: true,
    suppressSizeToFit: true,
};

export const COLUMN_ACTION_TYPE: ColDef = {
    headerName: 'Action type',
    field: 'actionType',
    width: 160,
    suppressSizeToFit: true,
    valueFormatter: actionTypeFormatter,
};

export const COLUMN_STATUS: ColDef = {
    headerName: 'Status',
    field: 'state',
    width: 60,
    resizable: false,
    suppressSizeToFit: true,
    cellRendererFramework: SwitchButtonCellComponent,
    cellRendererParams: {
        getSwitchValue: item => item.state === RuleState.ENABLED,
        toggle: (componentParent: RulesView, item: Rule, value: boolean) => {
            componentParent.onRuleStateToggle(item, value);
        },
        isReadOnly: (componentParent: RulesView, item: Rule) => {
            return componentParent.store.isReadOnly(item);
        },
    } as SwitchButtonRendererParams<Rule, RulesView>,
};

export const COLUMN_ACTION_FREQUENCY: ColDef = {
    headerName: 'Action frequency',
    field: 'actionFrequency',
    width: 110,
    resizable: true,
    suppressSizeToFit: true,
    valueFormatter: actionFrequencyFormatter,
};

export const COLUMN_NOTIFICATION: ColDef = {
    headerName: 'Notification',
    field: 'notificationType',
    width: 140,
    resizable: true,
    suppressSizeToFit: true,
    valueFormatter: notificationTypeFormatter,
};

export const COLUMN_RUNS_ON: ColDef = {
    headerName: 'Runs on',
    width: 200,
    suppressSizeToFit: true,
    resizable: true,
    cellRendererFramework: RuleRunsOnCellComponent,
    cellRendererParams: {
        getEntities: (rule: Rule) => getMappedEntities(rule.entities),
    },
};

export const COLUMN_RUNS_ON_TOOLTIP: ColDef = {
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

export const COLUMN_ACTIONS: ColDef = {
    headerName: '',
    cellRendererFramework: RuleActionsCellComponent,
    pinned: 'right',
    width: 75,
    suppressSizeToFit: true,
    resizable: true,
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
    const actionConfig: RuleActionConfig = RULE_ACTIONS_OPTIONS[params.value];
    return actionConfig?.valueLabel || 'N/A';
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
