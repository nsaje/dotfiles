import {ColDef} from 'ag-grid-community';
import {dateTimeFormatter} from '../../../../shared/helpers/grid.helpers';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';

export const COLUMN_DATE_CREATE: ColDef = {
    headerName: 'Date',
    field: 'createdDt',
    width: 120,
    minWidth: 120,
    resizable: false,
    valueFormatter: dateTimeFormatter('MM/DD/YYYY'),
};

export const COLUMN_RULE_NAME: ColDef = {
    headerName: 'Rule Name',
    field: 'ruleName',
    width: 200,
    minWidth: 200,
    resizable: false,
};

export const COLUMN_AD_GROUP_NAME: ColDef = {
    headerName: 'Ad Group Name',
    field: 'adGroupName',
    width: 200,
    minWidth: 200,
    resizable: false,
};

export const COLUMN_CHANGES_FORMATTED: ColDef = {
    headerName: 'Actions Taken',
    field: 'changesFormatted',
    width: 80,
    minWidth: 80,
    resizable: false,
    cellRendererFramework: IconTooltipCellComponent,
    cellRendererParams: {
        icon: IconTooltipCellIcon.Comment,
        placement: 'left',
    } as IconTooltipRendererParams,
};
