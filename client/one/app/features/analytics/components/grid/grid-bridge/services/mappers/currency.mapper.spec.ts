import {ValueFormatterParams, ValueGetterParams} from 'ag-grid-community';
import {Breakdown, Currency} from '../../../../../../../app.constants';
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
import * as smartGridHelpers from '../../../../../../../shared/components/smart-grid/helpers/smart-grid.helpers';
import {
    MAX_COLUMN_WIDTH,
    MIN_COLUMN_WIDTH,
    SMART_GRID_CELL_CURRENCY_CLASS,
    SMART_GRID_CELL_CURRENCY_REFUND_CLASS,
} from '../../grid-bridge.component.constants';
import {CellRole} from '../../../../../../../shared/components/smart-grid/smart-grid.component.constants';
import {CurrencyColumnMapper} from './currency.mapper';
import {CurrencyDataCellComponent} from '../../../cells/currency-data-cell/currency-data-cell.component';
import {CurrencyDataRendererParams} from '../../../cells/currency-data-cell/types/currency-data.renderer-params';
import {CurrencyRefundCellComponent} from '../../../cells/currency-refund-cell/currency-refund-cell.component';
import {CurrencyRefundRendererParams} from '../../../cells/currency-refund-cell/types/currency-refund.renderer-params';
import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';

describe('CurrencyColumnMapper', () => {
    let mapper: CurrencyColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new CurrencyColumnMapper();

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

    it('should correctly map non-editable currency grid column to smart grid column', () => {
        const colDef: SmartGridColDef = mapper.map(
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
        const expectedColDef: SmartGridColDef = {
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

    it('should correctly map editable currency grid column to smart grid column', () => {
        const editableMockedColumn: Partial<GridColumn> = {
            ...mockedColumn,
            data: {
                ...mockedColumn.data,
                editable: true,
            },
        };

        const colDef: SmartGridColDef = mapper.map(
            mockedGrid as Grid,
            editableMockedColumn as GridColumn
        );

        const columnWidth = smartGridHelpers.getApproximateColumnWidth(
            'Stats',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            false,
            true,
            true
        );
        const expectedColDef: SmartGridColDef = {
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
            cellClass: SMART_GRID_CELL_CURRENCY_CLASS,
            cellRendererFramework: CurrencyDataCellComponent,
            cellRendererParams: {
                getGrid: (params: CurrencyDataRendererParams) => {},
                setCurrencyData: (
                    value: string,
                    params: CurrencyDataRendererParams
                ) => {},
            } as CurrencyDataRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });

    it('should correctly map non-editable currency with refunds grid column to smart grid column', () => {
        const refundMockedGrid: Partial<Grid> = {
            ...mockedGrid,
            meta: {
                ...mockedGrid.meta,
                data: {
                    ...mockedGrid.meta.data,
                    breakdown: Breakdown.ACCOUNT,
                },
            },
        };

        const refundMockedColumn: Partial<GridColumn> = {
            ...mockedColumn,
            data: {
                ...mockedColumn.data,
                name: 'Media spend',
                field: 'e_media_cost',
            },
        };

        const colDef: SmartGridColDef = mapper.map(
            refundMockedGrid as Grid,
            refundMockedColumn as GridColumn
        );

        const columnWidth = smartGridHelpers.getApproximateColumnWidth(
            'Media spend',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            false,
            true,
            true
        );
        const expectedColDef: SmartGridColDef = {
            headerName: 'Media spend',
            field: 'e_media_cost',
            colId: 'e_media_cost',
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
            pinnedRowCellRendererFramework: CurrencyRefundCellComponent,
            pinnedRowCellRendererParams: {
                getRefundValueFormatted: (
                    params: CurrencyRefundRendererParams
                ) => {},
            } as CurrencyRefundRendererParams,
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            cellClassRules: {},
            cellClass: SMART_GRID_CELL_CURRENCY_REFUND_CLASS,
            cellRendererFramework: CurrencyRefundCellComponent,
            cellRendererParams: {
                getRefundValueFormatted: (
                    params: CurrencyRefundRendererParams
                ) => {},
            } as CurrencyRefundRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
