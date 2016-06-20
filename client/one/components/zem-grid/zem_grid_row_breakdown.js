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
            this.loadMore = function (size) {
                if (!size) {
                    size = this.row.data.pagination.count - this.row.data.pagination.limit;
                }
                this.grid.meta.service.loadData(this.row, size);
            };

            this.getBreakdownColumnStyle = function () {
                return zemGridUIService.getBreakdownColumnClass(this.row);
            };
        }],
    };
}]);
