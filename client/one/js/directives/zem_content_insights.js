/*globals oneApp*/
'use strict';

oneApp.directive('zemContentInsights', function () {
    return {
        restrict: 'E',
        scope: {
            rows: '=',
        },
        templateUrl: '/partials/zem_content_insights.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {

        }]
    };
});
