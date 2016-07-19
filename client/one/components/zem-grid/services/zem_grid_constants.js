/* globals oneApp */
'use strict';

oneApp.constant('zemGridConstants', {
    gridBodyRendering: {
        ROW_HEIGHT: 45,
        NUM_OF_ROWS_PER_PAGE: 11,
        NUM_OF_PRERENDERED_ROWS: 3,
    },
    gridColumnOrder: {
        NONE: 'none',
        ASC: 'asc',
        DESC: 'desc',
    },
    gridRowType: {
        STATS: 1,
        BREAKDOWN: 2,
        FOOTER: 3,
    },
    gridColumnTypes: {
        CHECKBOX: 'checkbox',
        BREAKDOWN: 'breakdown',
        BASE_FIELD: 'baseField',
        TEXT: 'text',
        PERCENT: 'percent',
        NUMBER: 'number',
        DATE_TIME: 'dateTime',
        SECONDS: 'seconds',
        CURRENCY: 'currency',
        INTERNAL_LINK: 'internalLink',
        STATUS: 'status',
        STATE_SELECTOR: 'stateSelector',
        PERFORMANCE_INDICATOR: 'performanceIndicator',
        SUBMISSION_STATUS: 'submissionStatus',
        THUMBNAIL: 'thumbnail',
        TEXT_WITH_POPUP: 'textWithPopup',
        TOTALS_LABEL: 'totalsLabel',
    },
    gridStyle: {
        CELL_PADDING: 8,
        BREAKDOWN_CELL_PADDING: 20,
        DEFAULT_ICON_SIZE: 20,
        DEFAULT_SCROLLER_WIDTH: 20,
    },
    gridSelectionFilterType: {
        NONE: 0,
        ALL: 1,
        CUSTOM: 2,
    },
    gridSelectionCustomFilterType: {
        ITEM: 1,
        LIST: 2,
    },
});
