import {IconTooltipDisplayOptions} from './types/icon-tooltip-display-options';

export enum IconTooltipCellIcon {
    Comment = 'zem-icon-tooltip-cell__icon--comment',
    Info = 'zem-icon-tooltip-cell__icon--info',
}

export enum IconTooltipCellTextStyleClass {
    Lighter = 'zem-icon-tooltip-cell__text--lighter',
}

export const DEFAULT_DISPLAY_OPTIONS: IconTooltipDisplayOptions<any> = {
    icon: IconTooltipCellIcon.Info,
    placement: 'top',
};
