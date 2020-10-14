import {GridOptions} from 'ag-grid-community';
import {DEFAULT_HEADER_CLASS} from './smart-grid.component.constants';
import {PageSizeConfig} from './types/page-size-config';

export const DEFAULT_GRID_OPTIONS: GridOptions = {
    headerHeight: 35,
    rowHeight: 35,
    domLayout: 'autoHeight',
    enableCellTextSelection: true,
    rowSelection: 'multiple',
    rowMultiSelectWithClick: true,
    suppressRowClickSelection: true,
    defaultColDef: {
        headerClass: [DEFAULT_HEADER_CLASS],
        suppressMovable: true,
        resizable: true,
    },
};

export const DEFAULT_PAGE_SIZE_OPTIONS: PageSizeConfig[] = [
    {name: '10', value: 10},
    {name: '20', value: 20},
    {name: '30', value: 30},
    {name: '50', value: 50},
    {name: '100', value: 100},
];
