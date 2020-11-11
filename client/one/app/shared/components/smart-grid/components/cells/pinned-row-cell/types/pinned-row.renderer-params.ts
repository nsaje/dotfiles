import {ICellRendererParams} from 'ag-grid-community';
import {Placement} from '../../../../../../types/placement';
import {CellRole} from '../../../../smart-grid.component.constants';
import {PinnedRowCellValueStyleClass} from '../pinned-row-cell.component.constants';

export interface PinnedRowRendererParams extends ICellRendererParams {
    popoverTooltip?: string;
    popoverPlacement?: Placement;
    valueStyleClass?: PinnedRowCellValueStyleClass;
    role?: CellRole;
}
