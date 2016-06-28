/* globals oneApp */
'use strict';

oneApp.factory('zemGridDataFormatter', ['$filter', 'zemGridConstants', function ($filter, zemGridConstants) {
    return {
        formatValue: formatValue,
    };

    function formatValue (value, options) {
        switch (options.type) {
        case zemGridConstants.gridColumnTypes.TEXT: return formatText(value, options);
        case zemGridConstants.gridColumnTypes.PERCENT: return formatPercent(value, options);
        case zemGridConstants.gridColumnTypes.SECONDS: return formatSeconds(value, options);
        case zemGridConstants.gridColumnTypes.DATE_TIME: return formatDateTime(value, options);
        case zemGridConstants.gridColumnTypes.NUMBER: return formatNumber(value, options);
        case zemGridConstants.gridColumnTypes.CURRENCY: return formatCurrency(value, options);
        default: return value || options.defaultValue || 'N/A';
        }
    }

    function formatText (value, options) {
        if (value !== 0 && !value) return options.defaultValue || '';
        return value + '';
    }

    function formatPercent (value, options) {
        if (value !== 0 && !value) return options.defaultValue || 'N/A';
        return $filter('number')(value, 2) + '%';
    }

    function formatSeconds (value, options) {
        if (value !== 0 && !value) return options.defaultValue || 'N/A';
        return $filter('number')(value, 1) + ' s';
    }

    function formatDateTime (value, options) {
        if (!value) return options.defaultValue || 'N/A';
        return $filter('date')(value, 'M/d/yyyy h:mm a', 'EST');
    }

    function formatNumber (value, options) {
        if (value !== 0 && !value) return options.defaultValue || 'N/A';
        var fractionSize = options.fractionSize || 0;
        return $filter('number')(value, fractionSize);
    }

    function formatCurrency (value, options) {
        if (value !== 0 && !value) return options.defaultValue || 'N/A';
        var fractionSize = options.fractionSize !== 0 && !options.fractionSize ? 2 : options.fractionSize;
        return $filter('decimalCurrency')(value, '$', fractionSize);
    }
}]);
