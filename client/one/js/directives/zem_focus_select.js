/*global $,oneApp,moment,constants*/
'use strict';

oneApp.directive('zemFocusSelect', ['$window', function ($window) {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            $window.setTimeout(function () {
                element[0].focus();
                element[0].setSelectionRange(0, element[0].value.length);
            }, 100);
        }
    };
}]);
