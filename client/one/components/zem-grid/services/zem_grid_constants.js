/* globals oneApp, angular */
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
    },
});
