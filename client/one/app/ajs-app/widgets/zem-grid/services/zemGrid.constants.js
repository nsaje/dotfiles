var GridColumnTypes = require('../../../../features/analytics/analytics.constants')
    .GridColumnTypes;
var GridRowType = require('../../../../features/analytics/analytics.constants')
    .GridRowType;
var GridRowLevel = require('../../../../features/analytics/analytics.constants')
    .GridRowLevel;
var GridRenderingEngineType = require('../../../../features/analytics/analytics.constants')
    .GridRenderingEngineType;
var GridSelectionFilterType = require('../../../../features/analytics/analytics.constants')
    .GridSelectionFilterType;

angular.module('one.widgets').factory('zemGridConstants', function() {
    var constants = {
        gridBodyRendering: {
            ROW_HEIGHT: 45,
            MIN_NUM_OF_ROWS_PER_PAGE: 25,
            NUM_OF_PRERENDERED_ROWS: 10,
        },
        gridColumnOrder: {
            NONE: 'none',
            ASC: 'asc',
            DESC: 'desc',
        },
        gridRowType: GridRowType,
        gridRowLevel: GridRowLevel,
        gridColumnTypes: GridColumnTypes,
        gridStyle: {
            CELL_PADDING: 8,
            BREAKDOWN_CELL_PADDING: 20,
            DEFAULT_ICON_SIZE: 20,
            DEFAULT_SCROLLER_WIDTH: 20,
            DEFAULT_MAX_COLUMN_WIDTH: 300,
            DEFAULT_MIN_COLUMN_WIDTH: 40,
        },
        gridSelectionFilterType: GridSelectionFilterType,
        gridSelectionCustomFilterType: {
            ITEM: 1,
            LIST: 2,
        },
        gridRenderingEngineType: GridRenderingEngineType,
    };

    constants.gridColumnTypes.BASE_TYPES = [
        GridColumnTypes.TEXT,
        GridColumnTypes.PERCENT,
        GridColumnTypes.NUMBER,
        GridColumnTypes.CURRENCY,
        GridColumnTypes.SECONDS,
        GridColumnTypes.DATE_TIME,
    ];

    constants.gridColumnTypes.EXTERNAL_LINK_TYPES = [
        GridColumnTypes.ICON_LINK,
        GridColumnTypes.VISIBLE_LINK,
        GridColumnTypes.TEXT_LINK,
    ];

    constants.gridColumnTypes.EXPORT_TYPES = [].concat(
        [constants.gridColumnTypes.BREAKDOWN, constants.gridColumnTypes.STATUS],
        constants.gridColumnTypes.BASE_TYPES,
        constants.gridColumnTypes.EXTERNAL_LINK_TYPES
    );

    return constants;
});
