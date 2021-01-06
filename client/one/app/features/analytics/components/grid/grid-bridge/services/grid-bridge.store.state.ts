import {SmartGridColDef} from '../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {PaginationOptions} from '../../../../../../shared/components/smart-grid/types/pagination-options';
import {Grid} from '../types/grid';
import {GridPagination} from '../types/grid-pagination';
import {GridRow} from '../types/grid-row';

export class GridBridgeStoreState {
    grid: Grid = null;
    columns: SmartGridColDef[] = [];
    columnsOrder: string[] = [];
    data = {
        rows: [] as GridRow[],
        totals: [] as GridRow[],
        paginationOptions: {
            type: null,
            page: null,
            pageSize: null,
        } as PaginationOptions,
        pagination: {
            complete: null,
            offset: null,
            limit: null,
            count: null,
        } as GridPagination,
    };
}
