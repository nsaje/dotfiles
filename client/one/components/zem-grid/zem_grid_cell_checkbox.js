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
            var maxRowsReached = false;

            var vm = this;
            vm.isDisabled = isDisabled;
            vm.toggleSelection = toggleSelection;

            this.grid.meta.api.onRowsSelectionChanged(this.grid.meta.scope, function () {
                maxRowsReached = false;
                var selectedRows = vm.grid.meta.api.getSelectedRows();
                var maxSelectedRows = vm.grid.meta.options.maxSelectedRows;
                if (maxSelectedRows && selectedRows.length >= maxSelectedRows) {
                    maxRowsReached = true;
                }
            });

            function isDisabled () {
                return maxRowsReached && !vm.row.selected;
            }

            function toggleSelection () {
                // Workaround - using the same field for checkbox ng-model as API (value is already updated)
                vm.grid.meta.api.setSelectedRows(vm.row, vm.row.selected);
            }
        }],
    };
}]);
