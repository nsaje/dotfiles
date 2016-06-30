/* global oneApp, $ */
'use strict';

oneApp.directive('zemScrollToTop', function () {
    return {
        restrict: 'A',
        scope: {
            api: '=zemScrollToTop',
        },
        link: function (scope, element) {
            scope.api.scroll = function () {
                $(element)[0].scrollTop = 0;
            };
        },
    };
});
