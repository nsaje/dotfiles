/*globals oneApp*/
'use strict';

function numberWithCommas (num) {
    var parts = num.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

oneApp.filter('decimalCurrency', function () {
    return function (input, sign, fractionSize, replaceTrailingZeros) {
        var num = parseFloat(input);

        if (!isNaN(num)) {
            fractionSize = parseInt(fractionSize);
            num = sign + num.toFixed(isNaN(fractionSize) ? 2 : fractionSize);

            if (replaceTrailingZeros !== undefined && replaceTrailingZeros !== null) {
                num = num.replace(/(\.{1}\d{2})([0]+)$/g, function (m, p1, p2) {
                    return p1 + p2.replace(/0/g, replaceTrailingZeros);
                });
            }

            return numberWithCommas(num);
        }
    };
});
