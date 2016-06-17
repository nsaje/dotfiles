/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellCollapse', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            col: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_collapse.html',
        controller: [function () {
            this.toggleCollapse = function () {
                this.grid.meta.api.setCollapsedRows(this.row, !this.row.collapsed);
            };
        }],
    };
}]);
