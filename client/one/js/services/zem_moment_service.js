/*globals angular,options,moment*/
'use strict';

angular.module('one.legacy').factory('zemMoment', function () {
    return function () {
        return moment.apply(this, arguments);
    };
});
