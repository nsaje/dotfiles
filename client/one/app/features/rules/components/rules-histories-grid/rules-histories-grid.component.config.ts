import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {LinkCellComponent} from '../../../../shared/components/smart-grid/components/cells/link-cell/link-cell.component';
import {RoutePathName, LevelParam} from '../../../../app.constants';
import {LinkRendererParams} from '../../../../shared/components/smart-grid/components/cells/link-cell/types/link.renderer-params';

export const COLUMN_DATE_CREATE: SmartGridColDef = {
    headerName: 'Run Date',
    field: 'createdDt',
    maxWidth: 90,
    minWidth: 90,
    resizable: true,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};

export const COLUMN_RULE_NAME: SmartGridColDef = {
    headerName: 'Rule Name',
    field: 'ruleName',
    width: 220,
    minWidth: 120,
    resizable: true,
};

export const COLUMN_AD_GROUP_NAME: SmartGridColDef = {
    headerName: 'Ad Group Name',
    field: 'adGroupName',
    width: 220,
    minWidth: 120,
    resizable: true,
    cellRendererFramework: LinkCellComponent,
    cellRendererParams: {
        getText: params => params.data.adGroupName,
        getLink: params =>
            `${RoutePathName.APP_BASE}/${RoutePathName.ANALYTICS}/${LevelParam.AD_GROUP}/${params.data.adGroupId}`,
    } as LinkRendererParams<RuleHistory>,
};

export const COLUMN_CHANGES_FORMATTED: SmartGridColDef = {
    headerName: 'Actions Taken',
    field: 'changesFormatted',
    width: 350,
    minWidth: 350,
    resizable: true,
};

export const COLUMN_CHANGES_FORMATTED_TOOLTIP: SmartGridColDef = {
    headerName: '',
    field: 'changesFormatted',
    maxWidth: 80,
    minWidth: 80,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        columnDisplayOptions: {
            icon: IconTooltipCellIcon.Comment,
            placement: 'left',
        },
    } as IconTooltipRendererParams<string, RuleHistory, any>,
};
