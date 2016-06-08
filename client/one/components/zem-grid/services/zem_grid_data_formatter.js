/* globals oneApp */
'use strict';

oneApp.factory('zemGridDataFormatter', ['$filter', function ($filter) {
    return {
        formatValue: formatValue,
    };

    function formatValue (value, options) {
        var formattedValue = value;

        switch (options.type) {
        case 'percent': formattedValue = formatPercent(value); break;
        case 'seconds': formattedValue = formatSeconds(value); break;
        case 'datetime': formattedValue = formatDateTime(value); break;
        case 'number': formattedValue = formatNumber(value, options); break;
        case 'currency': formattedValue = formatCurrency(value, options); break;
        }

        return formattedValue;
    }

    function formatPercent (value) {
        if (value !== 0 && !value) return 'N/A';
        return $filter('number')(value, 2) + '%';
    }

    function formatSeconds (value) {
        if (value !== 0 && !value) return 'N/A';
        return $filter('number')(value, 1) + ' s';
    }

    function formatDateTime (value) {
        if (!value) return 'N/A';
        return $filter('date')(value, 'M/d/yyyy h:mm a', 'EST');
    }

    function formatNumber (value, options) {
        if (value !== 0 && !value) return 'N/A';
        var fractionSize = options.fractionSize || 0;
        return $filter('number')(value, fractionSize);
    }

    function formatCurrency (value, options) {
        if (value !== 0 && !value) return 'N/A';
        var fractionSize = options.fractionSize !== 0 && !options.fractionSize ? 2 : options.fractionSize;
        return $filter('decimalCurrency')(value, '$', fractionSize);
    }
}]);
