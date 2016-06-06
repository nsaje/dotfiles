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
        controller: ['$scope', 'zemGridUIService', function ($scope, zemGridUIService) {
            this.toggleCollapse = function () {
                zemGridUIService.toggleCollapse(this.grid, this.row);
            };

            this.toggleSelection = function () {
                zemGridUIService.toggleSelection(this.grid, this.row);
            };
        }],
    };
}]);
