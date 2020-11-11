import {TemplateRef} from '@angular/core';
import {Placement} from '../../../../../../types/placement';
import {
    IconTooltipCellIcon,
    IconTooltipCellTextStyleClass,
} from '../icon-tooltip-cell.component.constants';

export interface IconTooltipDisplayOptions<T> {
    placement?: Placement;
    text?: string;
    textStyleClass?: IconTooltipCellTextStyleClass;
    textTooltip?: T;
    textTooltipTemplate?: TemplateRef<T>;
    icon?: IconTooltipCellIcon;
    iconTooltip?: T;
    iconTooltipTemplate?: TemplateRef<T>;
}
