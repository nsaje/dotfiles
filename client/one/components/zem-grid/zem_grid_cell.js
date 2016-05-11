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
            field: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['zemGridService', function (zemGridService) {
            this.toggleCollapse = function () {
                zemGridService.toggleCollapse(this.grid, this.row);
            };

            this.getCellStyle = function () {
                return zemGridService.getCellStyle(this.grid, this.position);
            };
        }],
    };
}]);
