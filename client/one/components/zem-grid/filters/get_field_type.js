/* globals oneApp */
'use strict';

oneApp.filter('getFieldType', ['zemGridConstants', function (zemGridConstants) {

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

        return columnType;
    };
}]);
