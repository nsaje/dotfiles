/*globals oneApp*/
'use strict';

oneApp.filter('groupColumnTypes', function () {

    return function (input) {
        input = input || '';
        if (['percent', 'number', 'currency', 'seconds', 'datetime'].indexOf(input) !== -1) {
            return 'base';
        }
        return input;
    };
});
