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
        controller: ['config', 'zemGridConstants', 'zemGridUIService', function (config, zemGridConstants, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;
            vm.config = config;
            vm.loadMore = loadMore;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;
            vm.getCompleteText = getCompleteText;

            function loadMore (size) {
                if (!size) {
                    size = vm.row.data.pagination.count - vm.row.data.pagination.limit;
                }
                vm.grid.meta.dataService.loadData(vm.row, size);
            }

            function getBreakdownColumnStyle () {
                return zemGridUIService.getBreakdownColumnStyle(vm.grid, vm.row);
            }

            function getCompleteText () {
                if (vm.row.type !== zemGridConstants.gridRowType.BREAKDOWN) return;

                var pagination = vm.row.data.pagination;
                if (vm.row.data.meta.error) return 'Error: Data can\'t be retrieved';
                if (pagination.count > 0) return 'All data loaded';
                if (pagination.count <= 0) return 'No data available';
            }
        }],
    };
}]);
