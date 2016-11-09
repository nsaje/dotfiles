/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridConstants', function () {

    var constants = {
        gridBodyRendering: {
            ROW_HEIGHT: 45,
            NUM_OF_ROWS_PER_PAGE: 41,
            NUM_OF_PRERENDERED_ROWS: 2,
        },
        gridColumnOrder: {
            NONE: 'none',
            ASC: 'asc',
            DESC: 'desc',
        },
        gridRowType: {
            STATS: 1,
            BREAKDOWN: 2,
        },
        gridRowLevel: {
            FOOTER: 0,
            BASE: 1,
            LEVEL_2: 2,
            LEVEL_3: 3,
            LEVEL_4: 4,
        },
        gridColumnTypes: {
            CHECKBOX: 'checkbox',
            BREAKDOWN: 'breakdown',
            BASE_FIELD: 'baseField',
            EDITABLE_BASE_FIELD: 'editableBaseField',
            TEXT: 'text',
            PERCENT: 'percent',
            NUMBER: 'number',
            DATE_TIME: 'dateTime',
            SECONDS: 'seconds',
            CURRENCY: 'currency',
            EXTERNAL_LINK: 'externalLink',
            ICON_LINK: 'link',
            VISIBLE_LINK: 'visibleLink',
            TEXT_LINK: 'linkText',
            INTERNAL_LINK: 'internalLink',
            STATUS: 'status',
            STATE_SELECTOR: 'stateSelector',
            PERFORMANCE_INDICATOR: 'performanceIndicator',
            SUBMISSION_STATUS: 'submissionStatus',
            THUMBNAIL: 'thumbnail',
            TOTALS_LABEL: 'totalsLabel',
        },
        gridStyle: {
            CELL_PADDING: 8,
            BREAKDOWN_CELL_PADDING: 20,
            DEFAULT_ICON_SIZE: 20,
            DEFAULT_SCROLLER_WIDTH: 20,
            DEFAULT_MAX_COLUMN_WIDTH: 300,
            DEFAULT_MIN_COLUMN_WIDTH: 40,
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
    };

    constants.gridColumnTypes.BASE_TYPES = [
        constants.gridColumnTypes.TEXT,
        constants.gridColumnTypes.PERCENT,
        constants.gridColumnTypes.NUMBER,
        constants.gridColumnTypes.CURRENCY,
        constants.gridColumnTypes.SECONDS,
        constants.gridColumnTypes.DATE_TIME,
    ];

    constants.gridColumnTypes.EXTERNAL_LINK_TYPES = [
        constants.gridColumnTypes.ICON_LINK,
        constants.gridColumnTypes.VISIBLE_LINK,
        constants.gridColumnTypes.TEXT_LINK,
    ];

    constants.gridColumnTypes.EXPORT_TYPES = [].concat(
        [constants.gridColumnTypes.BREAKDOWN, constants.gridColumnTypes.STATUS],
        constants.gridColumnTypes.BASE_TYPES,
        constants.gridColumnTypes.EXTERNAL_LINK_TYPES
    );

    return constants;
});
