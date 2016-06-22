/* globals oneApp */
'use strict';

oneApp.constant('zemGridConstants', {
    gridBodyRendering: {
        ROW_HEIGHT: 35,
        NUM_OF_ROWS_PER_PAGE: 15,
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
