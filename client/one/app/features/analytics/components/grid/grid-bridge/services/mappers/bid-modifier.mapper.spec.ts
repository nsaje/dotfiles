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
    BID_MODIFIER_COLUMN_WIDTH,
    SMART_GRID_CELL_BID_MODIFIER_CLASS,
} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {BidModifierColumnMapper} from './bid-modifier.mapper';
import {BidModifierGridCellComponent} from '../../../cells/bid-modifiers/bid-modifier-grid-cell/bid-modifier-grid-cell.component';
import {BidModifierRendererParams} from '../../../cells/bid-modifiers/bid-modifier-grid-cell/types/bid-modifier.renderer-params';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';

describe('BidModifierColumnMapper', () => {
    let mapper: BidModifierColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new BidModifierColumnMapper();

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
            type: GridColumnTypes.BID_MODIFIER_FIELD,
            data: {
                type: GridColumnTypes.BID_MODIFIER_FIELD,
                name: 'Bid modifier',
                field: 'bid_modifier',
                order: false,
                internal: false,
                help: 'Bid modifier help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map bid modifier grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: 'Bid modifier',
            field: 'bid_modifier',
            colId: GridColumnTypes.BID_MODIFIER_FIELD,
            minWidth: BID_MODIFIER_COLUMN_WIDTH,
            width: BID_MODIFIER_COLUMN_WIDTH,
            flex: 0,
            suppressSizeToFit: true,
            resizable: false,
            suppressMovable: false,
            pinned: null,
            lockPinned: true,
            headerComponentParams: {
                icon: null,
                internalFeature: false,
                enableSorting: false,
                sortOptions: {
                    sortType: 'server',
                    sort: HeaderCellSort.DESC,
                    orderField: null,
                    initialSort: null,
                    setSortModel: (sortModel: SortModel[]) => {},
                },
                popoverTooltip: 'Bid modifier help text',
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
            cellRendererFramework: BidModifierGridCellComponent,
            cellRendererParams: {
                getGrid: (params: BidModifierRendererParams) => {},
                setBidModifier: (
                    bidModifier: BidModifier,
                    params: BidModifierRendererParams
                ) => {},
            } as BidModifierRendererParams,
            cellClass: SMART_GRID_CELL_BID_MODIFIER_CLASS,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
