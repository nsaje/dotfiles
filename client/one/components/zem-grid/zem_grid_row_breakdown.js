/* globals oneApp */
'use strict';

oneApp.directive('zemGridRowBreakdown', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row_breakdown.html',
        controller: ['zemGridUIService', function (zemGridUIService) {
            var vm = this;
            vm.loadMore = loadMore;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;

            function loadMore (size) {
                if (!size) {
                    size = vm.row.data.pagination.count - vm.row.data.pagination.limit;
                }
                vm.grid.meta.service.loadData(vm.row, size);
            }

            function getBreakdownColumnStyle () {
                return zemGridUIService.getBreakdownColumnClass(vm.row);
            }
        }],
    };
}]);
