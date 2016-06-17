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
            this.toggleSelection = function () {
                // Workaround - using the same field for checkbox ng-model as API (value is already updated)
                this.grid.meta.api.setSelectedRows(this.row, this.row.selected);
            };
        }],
    };
}]);
