import {TemplateRef} from '@angular/core';
import {IconTooltipCellPlacement} from './icon-tooltip-cell-placement';
import {
    IconTooltipCellIcon,
    IconTooltipCellTextStyleClass,
} from '../icon-tooltip-cell.component.constants';

export interface IconTooltipDisplayOptions<T> {
    placement?: IconTooltipCellPlacement;
    icon?: IconTooltipCellIcon;
    text?: string;
    textStyleClass?: IconTooltipCellTextStyleClass;
    tooltip?: T;
    tooltipTemplate?: TemplateRef<T>;
}
