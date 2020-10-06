import {ICellRendererParams} from 'ag-grid-community';
import {IconTooltipDisplayOptions} from './icon-tooltip-display-options';

export interface IconTooltipRendererParams<T1, T2, T3>
    extends ICellRendererParams {
    data: T2;
    context: {componentParent?: T3};
    columnDisplayOptions: IconTooltipDisplayOptions<T1>;
    getCellDisplayOptions?: (
        data: T2,
        componentParent?: T3
    ) => Partial<IconTooltipDisplayOptions<T1>>;
}
