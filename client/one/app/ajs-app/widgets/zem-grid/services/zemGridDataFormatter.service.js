angular
    .module('one.widgets')
    .factory('zemGridDataFormatter', function(
        $filter,
        zemGridConstants,
        config
    ) {
        return {
            formatValue: formatValue,
            parseInputValue: parseInputValue,
            getCurrencySymbol: getCurrencySymbol,
        };

        function formatValue(value, options) {
            switch (options.type) {
                case zemGridConstants.gridColumnTypes.TEXT:
                    return formatText(value, options);
                case zemGridConstants.gridColumnTypes.PERCENT:
                    return formatPercent(value, options);
                case zemGridConstants.gridColumnTypes.SECONDS:
                    return formatSeconds(value, options);
                case zemGridConstants.gridColumnTypes.DATE_TIME:
                    return formatDateTime(value, options);
                case zemGridConstants.gridColumnTypes.NUMBER:
                    return formatNumber(value, options);
                case zemGridConstants.gridColumnTypes.CURRENCY:
                    return formatCurrency(value, options);
                case zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD:
                    return formatBidModifier(value, options);
                default:
                    return (
                        value ||
                        (options.defaultValue === undefined
                            ? 'N/A'
                            : options.defaultValue)
                    );
            }
        }

        function parseInputValue(value, options) {
            if (!options) {
                return value;
            }
            switch (options.type) {
                case zemGridConstants.gridColumnTypes.NUMBER:
                    return roundNumber(
                        value,
                        options,
                        constants.defaultFractionSize.NUMBER
                    );
                case zemGridConstants.gridColumnTypes.CURRENCY:
                    return roundNumber(
                        value,
                        options,
                        constants.defaultFractionSize.CURRENCY
                    );
                default:
                    return value;
            }
        }

        function formatText(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? ''
                    : options.defaultValue;
            }
            return value + '';
        }

        function formatPercent(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            return (
                $filter('number')(
                    value,
                    constants.defaultFractionSize.PERCENT
                ) + '%'
            );
        }

        function formatSeconds(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            return (
                $filter('number')(
                    value,
                    constants.defaultFractionSize.SECONDS
                ) + ' s'
            );
        }

        function formatDateTime(value, options) {
            if (!value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            return $filter('date')(value, 'M/d/yyyy h:mm a');
        }

        function formatNumber(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            var fractionSize;
            if (options.fractionSize !== 0 && !options.fractionSize) {
                fractionSize = constants.defaultFractionSize.NUMBER;
            } else {
                fractionSize = options.fractionSize;
            }
            return $filter('number')(value, fractionSize);
        }

        function formatCurrency(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            var fractionSize;
            if (options.fractionSize !== 0 && !options.fractionSize) {
                fractionSize = constants.defaultFractionSize.CURRENCY;
            } else {
                fractionSize = options.fractionSize;
            }
            return $filter('decimalCurrency')(
                value,
                getCurrencySymbol(options),
                fractionSize
            );
        }

        function formatBidModifier(value, options) {
            if (value !== 0 && !value) {
                return options.defaultValue === undefined
                    ? 'N/A'
                    : options.defaultValue;
            }
            value = value * 100 - 100; // Scale from [0, max] to [-100, 100 * max - 100] to display as percent.
            return (
                $filter('number')(
                    value,
                    constants.defaultFractionSize.PERCENT
                ) + '%'
            );
        }

        function roundNumber(value, options, defaultFractionSize) {
            if (value !== 0 && !value) {
                return;
            }
            var fractionSize;
            if (options.fractionSize !== 0 && !options.fractionSize) {
                fractionSize = defaultFractionSize;
            } else {
                fractionSize = options.fractionSize;
            }
            var number = parseFloat(value);
            if (!isNaN(number)) {
                return number.toFixed(fractionSize);
            }
        }

        function getCurrencySymbol(options) {
            if (!options.currency) {
                return config.currencySymbols[constants.currency.USD];
            }
            return config.currencySymbols[options.currency];
        }
    });
