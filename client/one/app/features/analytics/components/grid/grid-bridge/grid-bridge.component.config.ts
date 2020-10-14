import {GridColumnTypes} from '../../../analytics.constants';

export const RESIZABLE_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.BREAKDOWN,
    GridColumnTypes.TEXT,
    GridColumnTypes.PERCENT,
    GridColumnTypes.NUMBER,
    GridColumnTypes.DATE_TIME,
    GridColumnTypes.SECONDS,
    GridColumnTypes.CURRENCY,
    GridColumnTypes.EXTERNAL_LINK,
    GridColumnTypes.ICON_LINK,
    GridColumnTypes.VISIBLE_LINK,
    GridColumnTypes.TEXT_LINK,
    GridColumnTypes.INTERNAL_LINK,
];

export const PINNED_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.CHECKBOX,
    GridColumnTypes.ACTIONS,
    GridColumnTypes.BREAKDOWN,
];
