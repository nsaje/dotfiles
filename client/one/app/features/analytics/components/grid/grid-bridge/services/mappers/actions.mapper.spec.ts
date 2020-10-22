import {ColDef} from 'ag-grid-community';
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
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {BreakdownRendererParams} from '../../../cells/breakdown-cell/types/breakdown.renderer-params';
import {ActionsColumnMapper} from './actions.mapper';
import {ActionsCellComponent} from '../../../cells/actions-cell/actions-cell.component';
import {ActionsRendererParams} from '../../../cells/actions-cell/types/actions.renderer-params';
import {BREAKDOWN_TO_ACTIONS_COLUMN_WIDTH} from '../../grid-bridge.component.config';

describe('ActionsColumnMapper', () => {
    let mapper: ActionsColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new ActionsColumnMapper();

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
                    breakdown: Breakdown.ACCOUNT,
                },
                scope: null,
            },
        };
        mockedColumn = {
            type: GridColumnTypes.ACTIONS,
            data: {
                type: GridColumnTypes.ACTIONS,
                name: 'Actions',
                shown: true,
            },
        };
    });

    it('should correctly map breakdown grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: 'Actions',
            field: GridColumnTypes.ACTIONS,
            colId: GridColumnTypes.ACTIONS,
            minWidth: BREAKDOWN_TO_ACTIONS_COLUMN_WIDTH[Breakdown.ACCOUNT],
            width: BREAKDOWN_TO_ACTIONS_COLUMN_WIDTH[Breakdown.ACCOUNT],
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
            } as HeaderParams,
            valueFormatter: '',
            valueGetter: '',
            pinnedRowCellRendererFramework: PinnedRowCellComponent,
            pinnedRowCellRendererParams: {
                valueStyleClass: null,
                popoverTooltip: null,
                popoverPlacement: 'top',
            } as PinnedRowRendererParams,
            pinnedRowValueFormatter: '',
            cellRendererFramework: ActionsCellComponent,
            cellRendererParams: {
                getGrid: (params: BreakdownRendererParams) => {
                    return null;
                },
                getGridRow: (params: BreakdownRendererParams) => {
                    return null;
                },
            } as ActionsRendererParams,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
