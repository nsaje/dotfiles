/* globals oneApp */
'use strict';

oneApp.directive('zemContentInsights', function () {
    return {
        restrict: 'E',
        scope: {
            summary: '=',
            metric: '=',
            bestPerformerRows: '=',
            worstPerformerRows: '=',
        },
        templateUrl: '/partials/zem_content_insights.html',
    };
});
