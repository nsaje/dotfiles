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
            var vm = this;
            vm.toggleCollapse = toggleCollapse;

            function toggleCollapse () {
                vm.grid.meta.api.setCollapsedRows(vm.row, !vm.row.collapsed);
            }
        }],
    };
}]);
