/*globals oneApp*/
'use strict';

oneApp.filter('decimalCurrency', function () {
    return function (input, sign, fractionSize, replaceTrailingZeros) {
        var num = parseFloat(input);

        if (!isNaN(num)) {
            num = sign + num.toFixed(fractionSize || 2);

            if (replaceTrailingZeros !== undefined && replaceTrailingZeros !== null) {
                num = num.replace(/(\.{1}\d{2})([0]+)$/g, function (m, p1, p2) {
                    return p1 + p2.replace(/0/g, replaceTrailingZeros);
                });
            }

            return num;
        }
    };
});
