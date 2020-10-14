import {GridColumnTypes} from '../../../../analytics.constants';
import {GridColumnData} from './grid-column-data';
import {GridColumnOrder} from './grid-column-order';

export interface GridColumn {
    type: GridColumnTypes; // Reuse data type - type of column (text, link, icon, etc.)
    field: string; // Reuse data field - some kind of id  (data retrieval, storage, etc.)
    data: GridColumnData; // Column metadata retrieved from endpoint (cloned to prevent circular references)
    visible: boolean; // Visibility flag
    disabled: boolean; // Disabled flag
    order: GridColumnOrder; // Order information
}
