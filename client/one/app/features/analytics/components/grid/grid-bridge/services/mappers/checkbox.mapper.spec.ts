import {ColDef} from 'ag-grid-community';
import {Currency} from '../../../../../../../app.constants';
import {CheckboxCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {CheckboxRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/types/checkbox.renderer-params';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {
    GridColumnTypes,
    GridRenderingEngineType,
} from '../../../../../analytics.constants';
import {CHECKBOX_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
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
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: '',
            field: GridColumnTypes.CHECKBOX,
            colId: GridColumnTypes.CHECKBOX,
            minWidth: CHECKBOX_COLUMN_WIDTH,
            width: CHECKBOX_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
            pinned: 'left',
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
