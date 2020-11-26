import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {Breakdown, Currency} from '../../../../../../../app.constants';
import {CheckboxCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {CheckboxRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/types/checkbox.renderer-params';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {
    GridColumnTypes,
    GridRenderingEngineType,
} from '../../../../../analytics.constants';
import {CheckboxFilterHeaderCellComponent} from '../../../cells/checkbox-filter-header-cell/checkbox-filter-header-cell.component';
import {CheckboxFilterHeaderParams} from '../../../cells/checkbox-filter-header-cell/types/checkbox-filter-header-params';
import {
    CHECKBOX_COLUMN_WIDTH,
    CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {CheckboxColumnMapper} from './checkbox.mapper';

describe('CheckboxColumnMapper', () => {
    let mapper: CheckboxColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new CheckboxColumnMapper();

        mockedGrid = {
            meta: {
                initialized: true,
                loading: false,
                renderingEngine: GridRenderingEngineType.SMART_GRID,
                paginationOptions: null,
                options: null,
                api: null,
                dataService: null,
                columnsService: null,
                orderService: null,
                collapseService: null,
                selectionService: null,
                pubsub: null,
                data: {
                    ext: {
                        currency: Currency.USD,
                    },
                },
                scope: null,
            },
        };
        mockedColumn = {
            type: GridColumnTypes.CHECKBOX,
        };
    });

    it('should correctly map checkbox grid column to smart grid column', () => {
        const colDef: SmartGridColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: SmartGridColDef = {
            headerName: '',
            field: GridColumnTypes.CHECKBOX,
            colId: GridColumnTypes.CHECKBOX,
            minWidth: CHECKBOX_COLUMN_WIDTH,
            width: CHECKBOX_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
            suppressMovable: true,
            pinned: 'left',
            lockPinned: true,
            headerComponentParams: {
                icon: null,
                internalFeature: false,
                enableSorting: false,
                sortOptions: {
                    sortType: 'server',
                    sort: HeaderCellSort.NONE,
                    orderField: null,
                    initialSort: null,
                    setSortModel: (sortModel: SortModel[]) => {},
                },
                popoverTooltip: null,
                popoverPlacement: 'top',
                enableSelection: true,
                selectionOptions: {
                    isChecked: (params: HeaderParams) => {},
                    isDisabled: (params: HeaderParams) => {},
                    setChecked: (value: boolean, params: HeaderParams) => {},
                },
            } as HeaderParams,
            valueFormatter: '',
            valueGetter: '',
            pinnedRowCellRendererFramework: CheckboxCellComponent,
            pinnedRowCellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
            pinnedRowValueFormatter: '',
            lockPosition: true,
            cellRendererFramework: CheckboxCellComponent,
            cellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });

    it('should correctly map checkbox with filter grid column to smart grid column', () => {
        const mockedGridWithFilters: Partial<Grid> = {
            ...mockedGrid,
            meta: {
                ...mockedGrid.meta,
                data: {
                    ...mockedGrid.meta.data,
                    breakdown: Breakdown.CONTENT_AD,
                },
            },
        };

        const colDef: SmartGridColDef = mapper.map(
            mockedGridWithFilters as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: SmartGridColDef = {
            headerName: '',
            field: GridColumnTypes.CHECKBOX,
            colId: GridColumnTypes.CHECKBOX,
            minWidth: CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
            width: CHECKBOX_WITH_FILTERS_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
            suppressMovable: true,
            pinned: 'left',
            lockPinned: true,
            headerComponentFramework: CheckboxFilterHeaderCellComponent,
            headerComponentParams: {
                isChecked: (params: CheckboxFilterHeaderParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxFilterHeaderParams
                ) => {},
                getCustomFilters: (params: CheckboxFilterHeaderParams) => {},
                setCustomFilter: (
                    value: any,
                    params: CheckboxFilterHeaderParams
                ) => {},
            } as CheckboxFilterHeaderParams | HeaderParams,
            valueFormatter: '',
            valueGetter: '',
            pinnedRowCellRendererFramework: CheckboxCellComponent,
            pinnedRowCellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
            pinnedRowValueFormatter: '',
            lockPosition: true,
            cellRendererFramework: CheckboxCellComponent,
            cellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
