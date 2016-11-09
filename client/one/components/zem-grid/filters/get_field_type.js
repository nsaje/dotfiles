/* globals angular */
'use strict';

angular.module('one.legacy').filter('getFieldType', function (zemGridConstants) {

    return function (column) {
        if (!column) {
            return zemGridConstants.gridColumnTypes.BASE_FIELD;
        }

        var columnType = column.type || zemGridConstants.gridColumnTypes.BASE_FIELD;

        if (zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(columnType) !== -1) {
            if (column.data && column.data.editable) {
                return zemGridConstants.gridColumnTypes.EDITABLE_BASE_FIELD;
            }
            return zemGridConstants.gridColumnTypes.BASE_FIELD;
        }

        if (zemGridConstants.gridColumnTypes.EXTERNAL_LINK_TYPES.indexOf(columnType) !== -1) {
            return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
        }

        return columnType;
    };
});
