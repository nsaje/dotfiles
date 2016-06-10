/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridUIService', ['$timeout', 'zemGridConstants', function ($timeout, zemGridConstants) {

    var requestAnimationFrame = (function () {
        return window.requestAnimationFrame ||
            window.webkitRequestAnimationFrame ||
            window.mozRequestAnimationFrame ||
            window.oRequestAnimationFrame ||
            window.msRequestAnimationFrame ||
            function (callback) {
                window.setTimeout(callback, 1000 / 60);
            };
    })();

    function calculateColumnsWidths (grid, element) {
        // TODO: Optimize element querying
        var rows = element.find('.zem-grid-row');
        rows.each(function (rowIndex, row) {
            row = angular.element(row);
            var cells = row.find('.zem-grid-cell');
            cells.each(function (cellIndex, cell) {
                angular.element(cell).css({
                    'width': 'auto',
                });
                var cellWidth = cell.offsetWidth;
                if (!grid.ui.columnsWidths[cellIndex] || grid.ui.columnsWidths[cellIndex] < cellWidth) {
                    grid.ui.columnsWidths[cellIndex] = cellWidth;
                }
            });
            if (row.hasClass('breakdown')) {
                var paginationCell = row.find('.zem-grid-cell.pagination-cell');
                paginationCell.css({
                    'width': 'auto',
                });
                var paginationCellWidth = paginationCell[0].offsetWidth;
                if (!grid.ui.columnsWidths[0] || grid.ui.columnsWidths[0] < paginationCellWidth) {
                    grid.ui.columnsWidths[0] = paginationCellWidth;
                }
            }
        });
    }

    function resizeCells (grid, element) {
        // TODO: Optimize element querying
        var rows = element.find('.zem-grid-row');
        rows.each(function (rowIndex, row) {
            row = angular.element(row);
            var cells = row.find('.zem-grid-cell');
            cells.each(function (cellIndex, cell) {
                angular.element(cell).css({
                    'width': grid.ui.columnsWidths[cellIndex] + 'px',
                });
            });
            var paginationCell = row.find('.zem-grid-cell.pagination-cell');
            paginationCell.css({
                'width': grid.ui.columnsWidths[0] + 'px',
            });
            var loadMoreCell = row.find('.zem-grid-cell.load-more-cell');
            loadMoreCell.css({
                'width': 'auto',
            });
        });
    }

    function resizeGridColumns (grid) {
        requestAnimationFrame(function () {
            grid.ui.columnsWidths = [];

            calculateColumnsWidths(grid, grid.header.ui.element);
            calculateColumnsWidths(grid, grid.body.ui.element);
            calculateColumnsWidths(grid, grid.footer.ui.element);

            resizeCells(grid, grid.header.ui.element);
            resizeCells(grid, grid.body.ui.element);
            resizeCells(grid, grid.footer.ui.element);
        });
    }

    function getRowClass (grid, row) {
        var classes = [];
        classes.push('level-' + row.level);

        if (row.level === grid.meta.service.getBreakdownLevel()) {
            classes.push('level-last');
        }

        if (row.type === zemGridConstants.gridRowType.BREAKDOWN) {
            classes.push('breakdown');
        }
        return classes;
    }

    return {
        requestAnimationFrame: requestAnimationFrame,
        resizeGridColumns: resizeGridColumns,
        getRowClass: getRowClass,
    };
}]);
