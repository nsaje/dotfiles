/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCell', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            cell: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
