import {ColDef} from 'ag-grid-community';
import {PaginationOptions} from '../../../../../../shared/components/smart-grid/types/pagination-options';
import {Grid} from '../types/grid';
import {GridPagination} from '../types/grid-pagination';

export class GridBridgeStoreState {
    grid: Grid = null;
    columns: ColDef[] = [];
    data = {
        rows: [] as any[],
        totals: [] as any[],
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
