/* global oneApp, $ */
'use strict';

oneApp.directive('zemScrollToTop', function () {
    return {
        scope: {
            register: '=zemScrollToTop',
        },
        link: function (scope, element) {
            scope.register(function () {
                $(element)[0].scrollTop = 0;
            });
        },
    };
});
