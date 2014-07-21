'use strict'

oneApp.filter('decimalCurrency', function () {
    return function (input, sign, fractionSize) {
        var num = parseFloat(input);

        if (!isNaN(num)) {
            return sign + num.toFixed(fractionSize || 2);
        }
    }
});
