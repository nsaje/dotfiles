import {
    CellClassParams,
    ColDef,
    ValueFormatterParams,
    ValueGetterParams,
} from 'ag-grid-community';
import {Currency} from '../../../../../../../app.constants';
import {HeaderParams} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/header-params';
import {SortModel} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/types/sort-models';
import {PinnedRowCellComponent} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component';
import {PinnedRowRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/types/pinned-row.renderer-params';
import {
    GridColumnTypes,
    GridRenderingEngineType,
} from '../../../../../analytics.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {StatsDataColumnMapper} from './stats-data.mapper';
import * as smartGridHelpers from '../../../../../../../shared/components/smart-grid/helpers/smart-grid.helpers';
import {
    MAX_COLUMN_WIDTH,
    MIN_COLUMN_WIDTH,
} from '../../grid-bridge.component.constants';
import {CellRole} from '../../../../../../../shared/components/smart-grid/smart-grid.component.constants';

describe('StatsDataColumnMapper', () => {
    let mapper: StatsDataColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new StatsDataColumnMapper();

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
            type: GridColumnTypes.CURRENCY,
            data: {
                type: GridColumnTypes.CURRENCY,
                name: 'Stats',
                field: 'stats',
                order: true,
                internal: true,
                help: 'Stats help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map stats data grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const columnWidth = smartGridHelpers.getApproximateColumnWidth(
            'Stats',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            false,
            true,
            true
        );
        const expectedColDef: ColDef = {
            headerName: 'Stats',
            field: 'stats',
            colId: 'stats',
            minWidth: MIN_COLUMN_WIDTH,
            width: columnWidth,
            flex: 0,
            suppressSizeToFit: true,
            resizable: true,
            suppressMovable: false,
            pinned: null,
            lockPinned: true,
            headerComponentParams: {
                icon: null,
                internalFeature: true,
                enableSorting: true,
                sortOptions: {
                    sortType: 'server',
                    sort: HeaderCellSort.DESC,
                    orderField: null,
                    initialSort: null,
                    setSortModel: (sortModel: SortModel[]) => {},
                },
                popoverTooltip: 'Stats help text',
                popoverPlacement: 'top',
                role: CellRole.Metric,
            } as HeaderParams,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            valueGetter: (params: ValueGetterParams) => {
                return '';
            },
            pinnedRowCellRendererFramework: PinnedRowCellComponent,
            pinnedRowCellRendererParams: {
                valueStyleClass: null,
                popoverTooltip: null,
                popoverPlacement: 'top',
                role: CellRole.Metric,
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            cellClassRules: {},
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
