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
import {MIN_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {GridColumnOrder} from '../../types/grid-column-order';
import {HeaderCellSort} from '../../../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component.constants';
import {ExternalLinkColumnMapper} from './external-link.mapper';
import {EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_COLUMN_WIDTH} from '../../grid-bridge.component.config';
import {LinkRendererParams} from '../../../../../../../shared/components/smart-grid/components/cells/link-cell/types/link.renderer-params';
import {GridRow} from '../../types/grid-row';

describe('ExternalLinkColumnMapper', () => {
    let mapper: ExternalLinkColumnMapper;
    let mockedGrid: Partial<Grid>;
    let mockedColumn: Partial<GridColumn>;

    beforeEach(() => {
        mapper = new ExternalLinkColumnMapper();

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
            type: GridColumnTypes.ICON_LINK,
            data: {
                type: GridColumnTypes.ICON_LINK,
                name: 'SSPD Link',
                field: 'sspd_link',
                order: false,
                internal: true,
                help: 'SSPD Link help text',
                shown: true,
            },
            order: GridColumnOrder.DESC,
        };
    });

    it('should correctly map external link grid column to smart grid column', () => {
        const colDef: ColDef = mapper.map(
            mockedGrid as Grid,
            mockedColumn as GridColumn
        );

        const expectedColDef: ColDef = {
            headerName: 'SSPD Link',
            field: 'sspd_link',
            colId: 'sspd_link',
            minWidth: MIN_COLUMN_WIDTH,
            width:
                EXTERNAL_LINK_GRID_COLUMN_TYPES_TO_COLUMN_WIDTH[
                    GridColumnTypes.ICON_LINK
                ],
            flex: 0,
            suppressSizeToFit: true,
            resizable: true,
            pinned: null,
            headerComponentParams: {
                icon: null,
                internalFeature: true,
                enableSorting: false,
                sortOptions: {
                    sortType: 'server',
                    sort: HeaderCellSort.DESC,
                    orderField: null,
                    initialSort: null,
                    setSortModel: (sortModel: SortModel[]) => {},
                },
                popoverTooltip: 'SSPD Link help text',
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
            cellRendererParams: {
                getText: (params: LinkRendererParams<GridRow>) => {},
                getLink: (params: LinkRendererParams<GridRow>) => {},
                getLinkIcon: (params: LinkRendererParams<GridRow>) => {},
            } as LinkRendererParams<GridRow>,
        };

        expect(JSON.stringify(colDef)).toEqual(JSON.stringify(expectedColDef));
    });
});
