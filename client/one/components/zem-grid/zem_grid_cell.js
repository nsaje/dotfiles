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
        controller: [function () {
            this.toggleCollapse = function () {
                this.grid.meta.api.setCollapsedRows(this.row, !this.row.collapsed);
            };

            this.toggleSelection = function () {
                this.grid.meta.api.setSelectedRows(this.row, !this.row.selected);
            };
        }],
    };
}]);
