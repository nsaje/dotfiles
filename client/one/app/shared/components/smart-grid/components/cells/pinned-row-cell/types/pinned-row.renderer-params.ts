import {ICellRendererParams} from 'ag-grid-community';
import {PopoverPlacement} from '../../../../../popover/types/popover-placement';
import {CellRole} from '../../../../smart-grid.component.constants';
import {PinnedRowCellValueStyleClass} from '../pinned-row-cell.component.constants';

export interface PinnedRowRendererParams extends ICellRendererParams {
    popoverTooltip?: string;
    popoverPlacement?: PopoverPlacement;
    valueStyleClass?: PinnedRowCellValueStyleClass;
    role?: CellRole;
}
