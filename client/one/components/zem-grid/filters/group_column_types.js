/* globals oneApp */
'use strict';

oneApp.filter('groupColumnTypes', ['zemGridConstants', function (zemGridConstants) {
    // Filter is used to group different field types represented with the same directive.
    return function (input) {
        input = input || '';
        var baseColumnTypes = [
            zemGridConstants.gridColumnTypes.TEXT,
            zemGridConstants.gridColumnTypes.PERCENT,
            zemGridConstants.gridColumnTypes.NUMBER,
            zemGridConstants.gridColumnTypes.CURRENCY,
            zemGridConstants.gridColumnTypes.SECONDS,
            zemGridConstants.gridColumnTypes.DATE_TIME,
        ];
        if (baseColumnTypes.indexOf(input) !== -1) {
            return zemGridConstants.gridColumnTypes.BASE_FIELD;
        }
        return input;
    };
}]);
