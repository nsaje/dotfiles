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
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {StatusColumnMapper} from './status.mapper';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {STATUS_COLUMN_WIDTH} from '../../grid-bridge.component.constants';

describe('StatusColumnMapper', () => {
    let mapper: StatusColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new StatusColumnMapper();

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
            type: GridColumnTypes.STATUS,
            data: {
                type: GridColumnTypes.STATUS,
                name: 'Status',
                field: 'status',
                order: true,
                internal: true,
                help: 'Status help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map status grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: 'Status',
            field: 'status',
            colId: 'status',
            minWidth: STATUS_COLUMN_WIDTH,
            width: STATUS_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
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
                popoverTooltip: 'Status help text',
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
                valueStyleClass: null,
                popoverTooltip: null,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
