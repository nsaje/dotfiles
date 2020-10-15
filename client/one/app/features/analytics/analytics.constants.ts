export const GRID_ITEM_NOT_REPORTED = 'Not reported';

export enum GridRowType {
    STATS = 1,
    BREAKDOWN = 2,
    GROUP = 3,
}

export enum GridRowLevel {
    FOOTER = 0,
    BASE = 1,
    LEVEL_2 = 2,
    LEVEL_3 = 3,
    LEVEL_4 = 4,
}

export enum GridColumnTypes {
    CHECKBOX = 'checkbox',
    BREAKDOWN = 'breakdown',
    BASE_FIELD = 'baseField',
    EDITABLE_BASE_FIELD = 'editableBaseField',
    TEXT = 'text',
    PERCENT = 'percent',
    NUMBER = 'number',
    DATE_TIME = 'dateTime',
    SECONDS = 'seconds',
    CURRENCY = 'currency',
    EXTERNAL_LINK = 'externalLink',
    ICON_LINK = 'link',
    VISIBLE_LINK = 'visibleLink',
    TEXT_LINK = 'linkText',
    INTERNAL_LINK = 'internalLink',
    STATUS = 'status',
    STATE_SELECTOR = 'stateSelector',
    PERFORMANCE_INDICATOR = 'performanceIndicator',
    SUBMISSION_STATUS = 'submissionStatus',
    THUMBNAIL = 'thumbnail',
    TOTALS_LABEL = 'totalsLabel',
    ACTIONS = 'actions',
    BID_MODIFIER_FIELD = 'bid_modifier',
}

export enum GridRenderingEngineType {
    CUSTOM_GRID = 'custom-grid',
    SMART_GRID = 'smart-grid',
}

export enum GridSelectionFilterType {
    NONE = 0,
    ALL = 1,
    CUSTOM = 2,
}
