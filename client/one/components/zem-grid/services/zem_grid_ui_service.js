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

    function calculateColumnWidths (grid) {
        // Calculate rendered column widths, based on grid contents,
        // and configured styles (font, min/max widths, padding, etc.)
        // Solution is sub-optimal, since it can only calculate text fields (including parsed values)

        var headerCells = grid.header.ui.element.find('.zem-grid-cell');
        var font = window.getComputedStyle(headerCells[0], null).getPropertyValue('font');
        var padding = window.getComputedStyle(headerCells[0], null).getPropertyValue('padding-left');
        padding = parseInt(padding) || 0;

        var columnWidths = [];
        var maxColumnWidths = [];
        grid.header.visibleColumns.forEach(function (column, i) {
            var width = getTextWidth(column.data.name, font);
            if (column.data.help) width += 20; // TODO: find better solution for icon widths

            grid.body.rows.forEach(function (row) {
                if (row.type !== zemGridConstants.gridRowType.STATS) return;
                var valueWidth = getTextWidth(row.stats[column.field], font);
                width = Math.max(width, valueWidth);
            });

            if (grid.footer.row) {
                var valueWidth = getTextWidth(grid.footer.row.stats[column.field], font);
                width = Math.max(width, valueWidth);
            }

            // Final touch - use padding and check against min and max widths
            width += 2 * padding;
            var maxWidth = window.getComputedStyle(headerCells[0], null).getPropertyValue('max-width');
            var minWidth = window.getComputedStyle(headerCells[0], null).getPropertyValue('min-width');
            maxWidth = parseInt(maxWidth) || width;
            minWidth = parseInt(minWidth) || width;
            width = Math.min(maxWidth, width);
            width = Math.max(minWidth, width);

            maxColumnWidths[i] = maxWidth;
            columnWidths[i] = width;
        });

        var scrollerWidth = 20; // TODO: find exact value (based on browser version)
        var headerWidth = grid.header.ui.element[0].offsetWidth - scrollerWidth;
        keepAspectRatio(columnWidths, maxColumnWidths, headerWidth);

        grid.ui.columnsWidths = columnWidths;
    }

    function keepAspectRatio (columnWidths, maxColumnWidths, headerWidth) {
        // Stretch columns to fill available space, if there is any (keep ratio)
        while (true) { // eslint-disable-line no-constant-condition
            var computedColumnsWidth = 0;
            var maxedColumnsWidth = 0;
            columnWidths.forEach(function (w, i) {
                computedColumnsWidth += w;
                if (w >= maxColumnWidths[i]) maxedColumnsWidth += w;
            });

            if (maxedColumnsWidth === computedColumnsWidth || headerWidth <= computedColumnsWidth) break;

            var ratio = (headerWidth - maxedColumnsWidth) / (computedColumnsWidth - maxedColumnsWidth);
            columnWidths.forEach(function (w, i) {
                if (w < maxColumnWidths[i]) {
                    columnWidths[i] = Math.min(maxColumnWidths[i], w * ratio);
                }
            });
        }
    }

    function getTextWidth (text, font) {
        if (typeof text !== 'string') return -1;
        var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement('canvas'));
        var context = canvas.getContext('2d');
        context.font = font;
        var metrics = context.measureText(text);
        return metrics.width;
    }

    function resizeCells (grid, element) {
        var loadMoreColumnWidth = grid.ui.columnsWidths.reduce(function (sum, w, i) {
            if (i === 0) return 0; // Skip over first column
            return w + sum;
        }, 0);

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
                'width': loadMoreColumnWidth + 'px',
            });
        });
    }

    function resizeGridColumns (grid) {
        calculateColumnWidths(grid);
        resizeCells(grid, grid.ui.element);
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
