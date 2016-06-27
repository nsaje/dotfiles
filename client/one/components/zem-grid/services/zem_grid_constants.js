/* globals oneApp */
'use strict';

oneApp.constant('zemGridConstants', {
    gridBodyRendering: {
        ROW_HEIGHT: 45,
        NUM_OF_ROWS_PER_PAGE: 12,
        NUM_OF_PRERENDERED_ROWS: 3,
    },
    gridRowType: {
        STATS: 1,
        BREAKDOWN: 2,
        FOOTER: 3,
    },
    gridColumnType: {
        COLLAPSE: 'collapse',
        CHECKBOX: 'checkbox',
        BREAKDOWN: 'breakdown',
    },
    gridStyle: {
        CELL_PADDING: 8,
        BREAKDOWN_CELL_PADDING: 20,
        DEFAULT_ICON_SIZE: 20,
        DEFAULT_SCROLLER_WIDTH: 20,
    },
});
