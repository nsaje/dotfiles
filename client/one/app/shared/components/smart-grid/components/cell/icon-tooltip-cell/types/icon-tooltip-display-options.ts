import {TemplateRef} from '@angular/core';
import {IconTooltipCellPlacement} from './icon-tooltip-cell-placement';
import {
    IconTooltipCellIcon,
    IconTooltipCellTextStyleClass,
} from '../icon-tooltip-cell.component.constants';

export interface IconTooltipDisplayOptions<T> {
    placement?: IconTooltipCellPlacement;
    text?: string;
    textStyleClass?: IconTooltipCellTextStyleClass;
    textTooltip?: T;
    textTooltipTemplate?: TemplateRef<T>;
    icon?: IconTooltipCellIcon;
    iconTooltip?: T;
    iconTooltipTemplate?: TemplateRef<T>;
}
