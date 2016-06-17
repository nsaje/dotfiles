/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellCheckbox', [function () {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_checkbox.html',
        controller: [function () {
            this.onChange = function () {
                // Workaround - using the same field as API - remove the needed complexity
                this.grid.meta.api.setSelectedRows(this.row, this.row.selected);
            };
        }],
    };
}]);
