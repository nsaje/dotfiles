import {ColDef} from 'ag-grid-community';
import {Currency} from '../../../../../../../app.constants';
import {CheckboxCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {CheckboxRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/checkbox-cell/types/checkbox.renderer-params';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {
    GridColumnTypes,
    GridRenderingEngineType,
} from '../../../../../analytics.constants';
import {MIN_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
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
            sortable: false,
            sort: GridColumnOrder.NONE,
            minWidth: MIN_COLUMN_WIDTH,
            width: MIN_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
            pinned: true,
            headerComponentParams: {
                enableSelection: true,
                selectionOptions: {
                    isChecked: (params: HeaderParams) => {},
                    isDisabled: (params: HeaderParams) => {},
                    setChecked: (value: boolean, params: HeaderParams) => {},
                },
            } as HeaderParams,
            valueFormatter: '',
            pinnedRowCellRendererFramework: CheckboxCellComponent,
            pinnedRowCellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
            cellRendererFramework: CheckboxCellComponent,
            cellRendererParams: {
                isChecked: (params: CheckboxRendererParams) => {},
                isDisabled: (params: CheckboxRendererParams) => {},
                setChecked: (
                    value: boolean,
                    params: CheckboxRendererParams
                ) => {},
            } as CheckboxRendererParams,
            valueGetter: '',
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
