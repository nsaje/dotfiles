/* globals oneApp */
'use strict';

oneApp.filter('groupColumnTypes', function () {
    // Filter is used to group different field types represented with the same directive.
    return function (input) {
        input = input || '';
        if (['text', 'percent', 'number', 'currency', 'seconds', 'datetime'].indexOf(input) !== -1) {
            return 'base';
        }
        return input;
    };
});
