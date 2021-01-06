export const GRID_API_DEBOUNCE_TIME = 5;
export const GRID_API_LOADING_DATA_ERROR_MESSAGE = `Error: Data can't be retrieved`;

export const MIN_COLUMN_WIDTH = 50;
export const MAX_COLUMN_WIDTH = 180;

export const CHECKBOX_COLUMN_WIDTH = 40;
export const CHECKBOX_WITH_FILTERS_COLUMN_WIDTH = 50;
export const BREAKDOWN_COLUMN_WIDTH = 300;
export const STATUS_COLUMN_WIDTH = 100;
export const PERFORMANCE_INDICATOR_COLUMN_WIDTH = 70;
export const SUBMISSION_STATUS_COLUMN_WIDTH = 85;
export const THUMBNAIL_COLUMN_WIDTH = 80;
export const BID_MODIFIER_COLUMN_WIDTH = 115;

export const TOTALS_LABELS = 'TOTALS';
export const TOTALS_LABEL_HELP_TEXT =
    'Totals displays the sum of all metrics and costs including those that incurred on archived ads, ad groups, campaigns or accounts.';

export const SMART_GRID_ROW_ARCHIVED_CLASS =
    'zem-grid-bridge__ag-row--archived';
export const SMART_GRID_CELL_METRIC_CLASS = 'zem-grid-bridge__ag-cell--metric';
export const SMART_GRID_CELL_BID_MODIFIER_CLASS =
    'zem-grid-bridge__ag-cell--bid-modifier';
export const SMART_GRID_CELL_CURRENCY_CLASS =
    'zem-grid-bridge__ag-cell--currency';
export const SMART_GRID_CELL_CURRENCY_REFUND_CLASS =
    'zem-grid-bridge__ag-cell--currency-refund';

export const LOCAL_STORAGE_NAMESPACE = 'zemGridBridge';
export const LOCAL_STORAGE_COLUMNS_KEY = 'columns';

export enum EntityStatus {
    ACTIVE = 'Active',
    PAUSED = 'Paused',
    BLACKLISTED = 'Blacklisted',
    WHITELISTED = 'Whitelisted',
    ARCHIVED = 'Archived',
}

export enum GridColumnField {
    MEDIA_SPEND_REFUND = 'e_media_cost_refund',
    ACTUAL_BASE_MEDIA_SPEND_REFUND = 'media_cost_refund',
    PLATFORM_SPEND_REFUND = 'et_cost_refund',
    ACTUAL_BASE_PLATFORM_SPEND_REFUND = 'at_cost_refund',
    SERVICE_FEE_REFUND = 'service_fee_refund',
    LICENSE_FEE_REFUND = 'license_fee_refund',
    MARGIN_REFUND = 'margin_refund',
    AGENCY_SPEND_REFUND = 'etf_cost_refund',
    YESTERDAY_SPEND_REFUND = 'etfm_cost_refund',
}
