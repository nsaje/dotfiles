import {ICellRendererParams} from 'ag-grid-community';
import {IconTooltipCellIcon} from '../icon-tooltip-cell.component.constants';

export interface IconTooltipRendererParams extends ICellRendererParams {
    icon: IconTooltipCellIcon;
    placement?: string;
}
