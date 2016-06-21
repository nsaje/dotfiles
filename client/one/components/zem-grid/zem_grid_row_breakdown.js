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
        controller: ['zemGridConstants', 'zemGridUIService', function (zemGridConstants, zemGridUIService) {
            var vm = this;
            vm.loadMore = loadMore;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;
            vm.getPaginationText = getPaginationText;
            vm.getCompleteText = getCompleteText;

            function loadMore (size) {
                if (!size) {
                    size = vm.row.data.pagination.count - vm.row.data.pagination.limit;
                }
                vm.grid.meta.service.loadData(vm.row, size);
            }

            function getBreakdownColumnStyle () {
                return zemGridUIService.getBreakdownColumnStyle(vm.row);
            }

            function getPaginationText () {
                if (vm.row.type !== zemGridConstants.gridRowType.BREAKDOWN) return;

                var pagination = vm.row.data.pagination;
                if (vm.row.data.meta.loading) return 'Loading ...';
                if (pagination.count > 0) return '- ' + pagination.limit + ' of ' + pagination.count + ' -';
                return '- ' + pagination.limit + ' -';
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
