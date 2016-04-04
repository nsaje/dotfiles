/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridBody', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            rows: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
