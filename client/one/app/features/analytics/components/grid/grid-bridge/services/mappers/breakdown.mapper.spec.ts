import {
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
import {
    BREAKDOWN_COLUMN_WIDTH,
    TOTALS_LABEL_HELP_TEXT,
} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {BreakdownColumnMapper} from './breakdown.mapper';
import {BreakdownCellComponent} from '../../../cells/breakdown-cell/breakdown-cell.component';
import {BreakdownRendererParams} from '../../../cells/breakdown-cell/types/breakdown.renderer-params';
import {PinnedRowCellValueStyleClass} from '../../../../../../../shared/components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component.constants';

describe('BreakdownColumnMapper', () => {
    let mapper: BreakdownColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new BreakdownColumnMapper();

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
                name: 'Breakdown',
                field: 'breakdown',
                order: true,
                internal: true,
                help: 'Breakdown help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map breakdown grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: 'Breakdown',
            field: 'breakdown',
            colId: GridColumnTypes.BREAKDOWN,
            minWidth: BREAKDOWN_COLUMN_WIDTH,
            width: BREAKDOWN_COLUMN_WIDTH,
            flex: 1,
            suppressSizeToFit: false,
            resizable: true,
            suppressMovable: true,
            pinned: 'left',
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
                popoverTooltip: 'Breakdown help text',
                popoverPlacement: 'top',
            } as HeaderParams,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            valueGetter: (params: ValueGetterParams) => {
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
            lockPosition: true,
            cellRendererFramework: BreakdownCellComponent,
            cellRendererParams: {
                getEntity: (params: BreakdownRendererParams) => {},
                getPopoverTooltip: (params: BreakdownRendererParams) => {},
                navigateByUrl: (
                    params: BreakdownRendererParams,
                    url: string
                ) => {},
            } as BreakdownRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
