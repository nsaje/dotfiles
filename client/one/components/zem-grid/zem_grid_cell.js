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
        controller: ['$scope', 'zemGridApiService', function ($scope, zemGridInteractionService) {
            this.toggleCollapse = function () {
                zemGridInteractionService.toggleCollapse(this.grid, this.row);
            };

            this.toggleSelection = function () {
                zemGridInteractionService.toggleSelection(this.grid, this.row);
            };
        }],
    };
}]);
