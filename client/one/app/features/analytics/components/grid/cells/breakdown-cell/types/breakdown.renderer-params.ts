import {ICellRendererParams} from 'ag-grid-community';
import {PopoverPlacement} from '../../../../../../../shared/components/popover/types/popover-placement';

export interface BreakdownRendererParams extends ICellRendererParams {
    getPopoverTooltip?: (params: BreakdownRendererParams) => string;
    popoverPlacement?: PopoverPlacement;
}
