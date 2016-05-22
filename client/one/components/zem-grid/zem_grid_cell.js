/* globals oneApp */
'use strict';

oneApp.directive('zemGridCell', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            position: '=',
            col: '=',
            value: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['$scope', 'zemGridService', 'zemGridUIService', function ($scope, zemGridService, zemGridUIService) {
            this.toggleCollapse = function () {
                zemGridService.toggleCollapse(this.grid, this.row);
            };
        }],
    };
}]);
