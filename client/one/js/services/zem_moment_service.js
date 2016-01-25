/*globals angular,oneApp,options,moment*/
'use strict';

oneApp.factory('zemMoment', function () {
    return function () {
        return moment.apply(this, arguments);
    };
});
