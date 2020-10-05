import {GridPagination} from './grid-pagination';
import {GridRow} from './grid-row';

export interface GridBody {
    rows: GridRow[]; // flatten DataSource data (breakdown tree); see createRow() for row fields def.
    pagination: GridPagination; // pagination data
}
