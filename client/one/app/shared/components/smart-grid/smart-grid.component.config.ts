import {GridOptions} from 'ag-grid-community';
import {PageSizeConfig} from './types/page-size-config';

export const DEFAULT_GRID_OPTIONS: GridOptions = {
    headerHeight: 40,
    rowHeight: 40,
    domLayout: 'autoHeight',
    enableCellTextSelection: true,
    ensureDomOrder: false,
    animateRows: false,
    suppressAnimationFrame: true,
    suppressColumnMoveAnimation: false,
    suppressDragLeaveHidesColumns: true,
    rowSelection: 'multiple',
    rowMultiSelectWithClick: true,
    suppressRowClickSelection: true,
    suppressChangeDetection: false,
    defaultColDef: {
        suppressMovable: true,
        resizable: false,
    },
    cellFlashDelay: 100,
    cellFadeDelay: 1000,
};

export const DEFAULT_PAGE_SIZE_OPTIONS: PageSizeConfig[] = [
    {name: '10', value: 10},
    {name: '20', value: 20},
    {name: '30', value: 30},
    {name: '50', value: 50},
    {name: '100', value: 100},
];
