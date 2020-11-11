import {TemplateRef} from '@angular/core';
import {
    IconTooltipCellIcon,
    IconTooltipCellTextStyleClass,
} from '../icon-tooltip-cell.component.constants';
import {PopoverPlacement} from '../../../../../popover/types/popover-placement';

export interface IconTooltipDisplayOptions<T> {
    placement?: PopoverPlacement;
    text?: string;
    textStyleClass?: IconTooltipCellTextStyleClass;
    textTooltip?: T;
    textTooltipTemplate?: TemplateRef<T>;
    icon?: IconTooltipCellIcon;
    iconTooltip?: T;
    iconTooltipTemplate?: TemplateRef<T>;
}
