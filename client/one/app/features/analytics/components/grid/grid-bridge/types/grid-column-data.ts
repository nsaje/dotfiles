import {GridColumnTypes} from '../../../../analytics.constants';
import {GridColumnOrder} from './grid-column-order';

export interface GridColumnData {
    default?: boolean;
    defaultValue?: string;
    field?: string;
    help?: string;
    internal?: boolean;
    name?: string;
    order?: boolean;
    orderField?: string;
    initialOrder?: GridColumnOrder;
    shown: boolean;
    totalRow?: boolean;
    type: GridColumnTypes;
    editable?: boolean;
    fractionSize?: number;
}
