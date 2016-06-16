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
                var paginationElementWidth = 0;
                var loadMoreElementWidth = 0;
                var offset = (row.level-1) * 20 + 8;
                var found = false;
                grid.header.visibleColumns.forEach(function (column, idx) {
                    if (found) loadMoreElementWidth += grid.ui.columnsWidths[idx];
                    else paginationElementWidth += grid.ui.columnsWidths[idx];
                    if (column.type === 'breakdownName') {
                        offset = offset + paginationElementWidth - grid.ui.columnsWidths[idx];
                        found = true;
                    }
                });

                element.find('.pagination-cell').css ({
                    'width': paginationElementWidth + 'px',
                    'max-width': paginationElementWidth + 'px',
                    'padding-left': offset + 'px',
                });

                element.find('.load-more-cell').css({
                    'width': loadMoreElementWidth + 'px',
                    'max-width': loadMoreElementWidth + 'px',
                });
            });
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row_breakdown.html',
        controller: ['zemGridUIService', function (zemGridUIService) {
            this.loadMore = function (size) {
                if (!size) {
                    size = this.row.data.pagination.count - this.row.data.pagination.limit;
                }
                this.grid.meta.service.loadData(this.row, size);
            };
        }],
    };
}]);
