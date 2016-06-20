/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridUIService', ['$timeout', 'zemGridConstants', 'zemGridDataFormatter', function ($timeout, zemGridConstants, zemGridDataFormatter) { // eslint-disable-line max-len

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
        var gridWidth = 0;
        var columnWidths = [];
        var maxColumnWidths = [];
        grid.header.visibleColumns.forEach(function (column, i) {
            // Retrieve properties that affects column width
            var font = window.getComputedStyle(headerCells[i], null).getPropertyValue('font');
            var padding = window.getComputedStyle(headerCells[i], null).getPropertyValue('padding-left');
            var maxWidth = window.getComputedStyle(headerCells[i], null).getPropertyValue('max-width');
            var minWidth = window.getComputedStyle(headerCells[i], null).getPropertyValue('min-width');
            maxWidth = parseInt(maxWidth) || Number.MAX_VALUE;
            minWidth = parseInt(minWidth) || 0;
            padding = parseInt(padding) || 0;

            // Calculate column column width without constraints (use only font)
            var width = calculateColumnWidth(grid, column, font);

            // Apply constraints to column width (padding, max/min size)
            width += 2 * padding;
            width = Math.min(maxWidth, width);
            width = Math.max(minWidth, width);

            maxColumnWidths[i] = maxWidth;
            columnWidths[i] = width;
            gridWidth += width;
        });

        var scrollerWidth = 20; // TODO: find exact value (based on browser version)
        var headerWidth = grid.header.ui.element[0].offsetWidth - scrollerWidth;
        keepAspectRatio(columnWidths, maxColumnWidths, headerWidth);
        gridWidth = Math.max(headerWidth, gridWidth);

        grid.ui.columnsWidths = columnWidths;
        grid.ui.width = gridWidth;
    }

    function calculateColumnWidth (grid, column, font) {
        if (!column.data) return -1;

        var width = getTextWidth(column.data.name, font);
        width = Math.max(width, 20);        // Column without text (e.g. only icon)
        if (column.data.help) width += 20;  // TODO: find better solution for icon widths

        grid.body.rows.forEach(function (row) {
            if (row.type !== zemGridConstants.gridRowType.STATS) return;
            var data = row.data.stats[column.field];
            if (data) {
                // Format data to string and predict width based on it
                var parsedValue = zemGridDataFormatter.formatValue(data.value, column);
                var valueWidth = getTextWidth(parsedValue, font);
                if (column.type === zemGridConstants.gridColumnType.BREAKDOWN) {
                    // Special case for breakdown column - add padding based on row level
                    valueWidth += (row.level - 1) * 20;
                }
                width = Math.max(width, valueWidth);
            }
        });

        if (grid.footer.row) {
            var data = grid.footer.row.data.stats[column.field];
            if (data) {
                var parsedValue = zemGridDataFormatter.formatValue(data.value, column);
                var valueWidth = getTextWidth(parsedValue, font);
                width = Math.max(width, valueWidth);
            }
        }

        return width;
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
        if (!getTextWidth.canvas) {
            getTextWidth.canvas = document.createElement('canvas');
        }
        var context = getTextWidth.canvas.getContext('2d');
        context.font = font;
        var metrics = context.measureText(text);
        return metrics.width;
    }

    function resizeCells (grid) {
        var element = grid.ui.element;
        var rows = element.find('.zem-grid-row');
        rows.each(function (rowIndex, row) {
            row = angular.element(row);
            var cells = row.find('.zem-grid-cell');
            cells.each(function (cellIndex, cell) {
                angular.element(cell).css({
                    'width': grid.ui.columnsWidths[cellIndex] + 'px',
                });
            });
        });
    }

    function resizeBreakdownRows (grid) {
        // Resize breakdown columns based on breakdown column position
        // Breakdown split widths - before breakdown (empty), breakdown (pagination), after breakdown (load-more)
        var element = grid.ui.element;
        var breakdownSplitWidths = [0];
        grid.header.visibleColumns.forEach(function (column, idx) {
            if (column.type === zemGridConstants.gridColumnType.BREAKDOWN) {
                breakdownSplitWidths.push(grid.ui.columnsWidths[idx]);
                breakdownSplitWidths.push(0);
                return;
            }
            breakdownSplitWidths[breakdownSplitWidths.length - 1] += grid.ui.columnsWidths[idx];
        });

        var paginationCellPadding = breakdownSplitWidths[0] + 8;
        var paginationCellWidth = breakdownSplitWidths[0] + breakdownSplitWidths[1];
        var loadMoreCellWidth = breakdownSplitWidths[2];
        element.find('.breakdown-pagination-cell').css({
            'width': paginationCellWidth + 'px',
            'max-width': paginationCellWidth + 'px',
            'padding-left': paginationCellPadding,
        });

        element.find('.breakdown-load-more-cell').css({
            'width': loadMoreCellWidth + 'px',
            'max-width': loadMoreCellWidth + 'px',
        });
    }

    function resizeGridColumns (grid) {
        calculateColumnWidths(grid);
        resizeCells(grid);
        resizeBreakdownRows(grid);
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

    function getHeaderColumnClass (grid, column) {
        var classes = [];
        classes.push('zem-grid-cell');

        if (column.type === zemGridConstants.gridColumnType.CHECKBOX) {
            classes.push('zem-grid-cell-checkbox');
        }

        if (column.type === zemGridConstants.gridColumnType.COLLAPSE) {
            classes.push('zem-grid-cell-collapse');
        }

        return classes;
    }

    function getBreakdownColumnStyle (row) {
        return {
            'padding-left': (row.level - 1) * 20 + 'px',
        };
    }

    return {
        requestAnimationFrame: requestAnimationFrame,
        resizeGridColumns: resizeGridColumns,
        getRowClass: getRowClass,
        getHeaderColumnClass: getHeaderColumnClass,
        getBreakdownColumnClass: getBreakdownColumnStyle,
    };
}]);
