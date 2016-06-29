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
        COLLAPSE: 'collapse',
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
        NOTIFICATION: 'notification',
        TOTALS_LABEL: 'totalsLabel',
    },
    gridStyle: {
        CELL_PADDING: 8,
        BREAKDOWN_CELL_PADDING: 20,
        DEFAULT_ICON_SIZE: 20,
        DEFAULT_SCROLLER_WIDTH: 20,
    },
});
