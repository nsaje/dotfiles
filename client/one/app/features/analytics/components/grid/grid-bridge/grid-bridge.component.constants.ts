export const GRID_API_DEBOUNCE_TIME = 5;
export const GRID_API_LOADING_DATA_ERROR_MESSAGE = `Error: Data can't be retrieved`;

export const TABLET_BREAKPOINT = 768;

export const MIN_COLUMN_WIDTH = 40;
export const MAX_COLUMN_WIDTH = 180;

export const CHECKBOX_COLUMN_WIDTH = 40;
export const BREAKDOWN_COLUMN_WIDTH = 300;
export const STATUS_COLUMN_WIDTH = 100;
export const PERFORMANCE_INDICATOR_COLUMN_WIDTH = 70;

export const TOTALS_LABELS = 'TOTALS';
export const TOTALS_LABEL_HELP_TEXT =
    'Totals displays the sum of all metrics and costs including those that incurred on archived ads, ad groups, campaigns or accounts.';

export const ARCHIVED_ROW_CLASS = 'zem-grid-bridge__row--archived';

export enum EntityStatus {
    ACTIVE = 'Active',
    PAUSED = 'Paused',
    BLACKLISTED = 'Blacklisted',
    WHITELISTED = 'Whitelisted',
    ARCHIVED = 'Archived',
}