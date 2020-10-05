import {GridColumn} from './grid-column';

export interface GridHeader {
    columns: GridColumn[]; // array of visible columns (subset of meta.data.columns)
}
