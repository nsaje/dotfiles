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
        link: function (scope, element) {
            var grid = scope.ctrl.grid;
            scope.$watch('ctrl.row', function (row) {
                // Resize breakdown columns based on breakdown column position
                // Breakdown split widths - before breakdown, breakdown, after breakdown
                var breakdownSplitWidths = [0];
                grid.header.visibleColumns.forEach(function (column, idx) {
                    if (column.type === 'breakdown') {
                        breakdownSplitWidths.push(grid.ui.columnsWidths[idx]);
                        breakdownSplitWidths.push(0);
                    }
                    breakdownSplitWidths[breakdownSplitWidths.length - 1] += grid.ui.columnsWidths[idx];
                });

                var paginationCellWidth = breakdownSplitWidths[0] + breakdownSplitWidths[1];
                var paginationPadding = breakdownSplitWidths[0] + (row.level - 1) * 20;
                var loadMoreCellWidth = breakdownSplitWidths[2];

                element.find('.breakdown-pagination-cell').css({
                    'width': paginationCellWidth + 'px',
                    'max-width': paginationCellWidth + 'px',
                    'padding-left': paginationPadding + 'px',
                });

                element.find('.breakdown-load-more-cell').css({
                    'width': loadMoreCellWidth + 'px',
                    'max-width': loadMoreCellWidth + 'px',
                });
            });
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row_breakdown.html',
        controller: [function () {
            this.loadMore = function (size) {
                if (!size) {
                    size = this.row.data.pagination.count - this.row.data.pagination.limit;
                }
                this.grid.meta.service.loadData(this.row, size);
            };
        }],
    };
}]);
