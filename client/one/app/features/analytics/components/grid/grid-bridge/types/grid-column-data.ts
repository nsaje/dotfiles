import {GridColumnTypes} from '../../../../analytics.constants';

export interface GridColumnData {
    default?: boolean;
    field?: string;
    help?: string;
    initialOrder?: 'none' | 'asc' | 'desc';
    internal: boolean;
    name: string;
    order?: boolean;
    orderField?: string;
    shown: boolean;
    totalRow: boolean;
    type: GridColumnTypes;
    editable?: boolean;
}
