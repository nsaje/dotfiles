angular
    .module('one.widgets')
    .factory('zemGridDataValidator', function(zemGridConstants) {
        return {
            validate: validate,
        };

        function validate(value, options) {
            var isValid = true;

            switch (options.type) {
                case zemGridConstants.gridColumnTypes.CURRENCY:
                    isValid = validateCurrency(value, options);
                    break;
            }

            return isValid;
        }

        function validateCurrency(value, options) {
            var fractionSize;
            if (options.fractionSize !== 0 && !options.fractionSize) {
                fractionSize = constants.defaultFractionSize.CURRENCY;
            } else {
                fractionSize = options.fractionSize;
            }

            var currencyRegex;
            if (fractionSize === 0) {
                currencyRegex = new RegExp('^\\d*$');
            } else {
                currencyRegex = new RegExp(
                    '^\\d*\\.?\\d{0,' + fractionSize + '}?$'
                );
            }

            if (currencyRegex.exec(value)) {
                if (options.maxValue) {
                    return (parseInt(value) || 0) <= options.maxValue;
                }
                return true;
            }
            return false;
        }
    });
