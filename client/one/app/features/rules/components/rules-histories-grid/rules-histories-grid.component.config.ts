import {ColDef} from 'ag-grid-community';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {LinkCellComponent} from '../../../../shared/components/smart-grid/components/cell/link-cell/link-cell.component';
import {RoutePathName, LevelParam} from '../../../../app.constants';
import {LinkRendererParams} from '../../../../shared/components/smart-grid/components/cell/link-cell/types/link.renderer-params';

export const COLUMN_DATE_CREATE: ColDef = {
    headerName: 'Run Date',
    field: 'createdDt',
    maxWidth: 120,
    minWidth: 120,
    resizable: false,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};

export const COLUMN_RULE_NAME: ColDef = {
    headerName: 'Rule Name',
    field: 'ruleName',
    width: 250,
    minWidth: 250,
    resizable: false,
};

export const COLUMN_AD_GROUP_NAME: ColDef = {
    headerName: 'Ad Group Name',
    field: 'adGroupName',
    width: 250,
    minWidth: 250,
    resizable: false,
    cellRendererFramework: LinkCellComponent,
    cellRendererParams: {
        getText: item => item.adGroupName,
        getLink: item =>
            `${RoutePathName.APP_BASE}/${RoutePathName.ANALYTICS}/${LevelParam.AD_GROUP}/${item.adGroupId}`,
    } as LinkRendererParams<RuleHistory>,
};

export const COLUMN_CHANGES_FORMATTED_PREVIEW: ColDef = {
    headerName: 'Actions Taken',
    field: 'changesFormatted',
    width: 350,
    minWidth: 350,
    resizable: false,
};

export const COLUMN_CHANGES_FORMATTED: ColDef = {
    headerName: '',
    field: 'changesFormatted',
    maxWidth: 80,
    minWidth: 80,
    resizable: false,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        icon: IconTooltipCellIcon.Comment,
        placement: 'left',
    } as IconTooltipRendererParams,
};
