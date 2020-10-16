import {ColDef, ValueFormatterParams} from 'ag-grid-community';
import {Currency} from '../../../../../../../app.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {PinnedRowCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component';
import {PinnedRowCellValueStyleClass} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component.constants';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';
import {
    GridColumnTypes,
    GridRenderingEngineType,
} from '../../../../../analytics.constants';
import {
    BREAKDOWN_MIN_COLUMN_WIDTH,
    NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN,
    NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
    TOTALS_LABEL_HELP_TEXT,
} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {ColumnMapper} from './column.mapper';
import {getApproximateGridColumnWidth} from '../../helpers/grid-bridge.helper';

class TestColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): ColDef {
        return null;
    }
}

describe('ColumnMapper', () => {
    let mapper: TestColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new TestColumnMapper();

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
            type: GridColumnTypes.BREAKDOWN,
            data: {
                type: GridColumnTypes.BREAKDOWN,
                name: 'Test Header',
                field: 'test_field',
                order: true,
                internal: true,
                help: 'Help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const approximateWidth: number = getApproximateGridColumnWidth(
            'Test Header',
            BREAKDOWN_MIN_COLUMN_WIDTH,
            NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
            NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
        );

        const expectedColDef: ColDef = {
            headerName: 'Test Header',
            field: 'test_field',
            colId: 'test_field',
            sortable: true,
            sort: GridColumnOrder.DESC,
            minWidth: BREAKDOWN_MIN_COLUMN_WIDTH,
            width: approximateWidth,
            flex: 1,
            suppressSizeToFit: false,
            resizable: true,
            pinned: 'left',
            headerComponentParams: {
                icon: null,
                internalFeature: true,
                sortOptions: {
                    sortType: 'server',
                    orderField: null,
                    initialSort: null,
                    setSortModel: (sortModel: SortModel[]) => {},
                },
                popoverTooltip: 'Help text',
                popoverPlacement: 'top',
            } as HeaderParams,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            pinnedRowCellRendererFramework: PinnedRowCellComponent,
            pinnedRowCellRendererParams: {
                valueStyleClass: PinnedRowCellValueStyleClass.Strong,
                popoverTooltip: TOTALS_LABEL_HELP_TEXT,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
