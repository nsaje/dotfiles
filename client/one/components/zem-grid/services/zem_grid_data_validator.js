/* globals oneApp */
'use strict';

oneApp.factory('zemGridDataValidator', ['zemGridConstants', function (zemGridConstants) {
    return {
        validate: validate,
    };

    function validate (value, options) {
        var isValid = true;

        switch (options.type) {
        case zemGridConstants.gridColumnTypes.CURRENCY: isValid = validateCurrency(value, options); break;
        }

        return isValid;
    }

    function validateCurrency (value, options) {
        var fractionSize = options.fractionSize || 2;
        var currencyRegex = new RegExp('^\\d*\\.?\\d{0,' + fractionSize + '}?$');
        if (currencyRegex.exec(value)) {
            return true;
        }
        return false;
    }
}]);
