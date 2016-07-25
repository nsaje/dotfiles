/* globals oneApp, angular, constants */
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
        headerCells.each(function (i) {
            // Retrieve properties that affects column width
            var font = window.getComputedStyle(headerCells[i], null).getPropertyValue('font');
            var padding = window.getComputedStyle(headerCells[i], null).getPropertyValue('padding-left');
            var maxWidth = window.getComputedStyle(headerCells[i], null).getPropertyValue('max-width');
            var minWidth = window.getComputedStyle(headerCells[i], null).getPropertyValue('min-width');
            maxWidth = parseInt(maxWidth) || Number.MAX_VALUE;
            minWidth = parseInt(minWidth) || 0;
            padding = parseInt(padding) || 0;

            // Calculate column column width without constraints (use only font)
            var width = calculateColumnWidth(grid, grid.header.visibleColumns[i], font);

            // Apply constraints to column width (padding, max/min size)
            width += 2 * padding;
            width = Math.min(maxWidth, width);
            width = Math.max(minWidth, width);

            maxColumnWidths[i] = maxWidth;
            columnWidths[i] = width;
            gridWidth += width;
        });

        var headerWidth = grid.header.ui.element[0].offsetWidth;
        if (grid.body.rows.length > zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE) {
            // Check if scroller will be present and incorporate this into header width
            headerWidth -= zemGridConstants.gridStyle.DEFAULT_SCROLLER_WIDTH;
        }
        keepAspectRatio(columnWidths, maxColumnWidths, headerWidth);
        gridWidth = Math.max(headerWidth, gridWidth);

        grid.ui.columnsWidths = columnWidths;
        grid.ui.width = gridWidth;
        grid.ui.headerWidth = headerWidth;
    }

    function calculateColumnWidth (grid, column, font) {
        if (!column || !column.data) return -1;

        var width = getTextWidth(column.data.name, font);
        width = Math.max(width, zemGridConstants.gridStyle.DEFAULT_ICON_SIZE);  // Column without text (e.g. only icon)
        if (column.data.internal) {
            width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
        }
        if (column.data.help) {
            width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
        }
        if (column.order !== zemGridConstants.gridColumnOrder.NONE) {
            width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
        }

        grid.body.rows.forEach(function (row) {
            if (row.type !== zemGridConstants.gridRowType.STATS) return;
            var data = row.data.stats[column.field];
            if (!data) return;

            // Format data to string and predict width based on it
            var formattedValue = zemGridDataFormatter.formatValue(data.value, column);
            var valueWidth = getTextWidth(formattedValue, font);
            if (column.type === zemGridConstants.gridColumnTypes.BREAKDOWN) {
                // Special case for breakdown column - add padding based on row level
                valueWidth += (row.level - 1) * zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
                // Add additional padding when collapse icon is shown
                if (grid.meta.dataService.getBreakdownLevel() > 1 && row.level > 0) {
                    valueWidth += zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
                }
            }
            width = Math.max(width, valueWidth);
        });

        if (grid.footer.row) {
            var data = grid.footer.row.data.stats[column.field];
            if (data) {
                var formattedValue = zemGridDataFormatter.formatValue(data.value, column);
                var valueWidth = getTextWidth(formattedValue, font);
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
            if (column.type === zemGridConstants.gridColumnTypes.BREAKDOWN) {
                breakdownSplitWidths.push(grid.ui.columnsWidths[idx]);
                breakdownSplitWidths.push(0);
                return;
            }
            breakdownSplitWidths[breakdownSplitWidths.length - 1] += grid.ui.columnsWidths[idx];
        });

        var paginationCellPadding = breakdownSplitWidths[0] + zemGridConstants.gridStyle.CELL_PADDING;
        var paginationCellWidth = breakdownSplitWidths[0] + breakdownSplitWidths[1];
        var loadMoreCellWidth = breakdownSplitWidths[2];

        if (breakdownSplitWidths.length === 1) {
            // Fallback if BREAKDOWN column has not been found
            paginationCellPadding = 50;
            paginationCellWidth = 200;
            loadMoreCellWidth = grid.ui.width - 250;
        }

        element.find('.breakdown-row-primary-cell').css({
            'width': paginationCellWidth + 'px',
            'max-width': paginationCellWidth + 'px',
            'padding-left': paginationCellPadding + 'px',
        });

        element.find('.breakdown-row-info-cell').css({
            'width': loadMoreCellWidth + 'px',
            'max-width': loadMoreCellWidth + 'px',
        });
    }

    function resizeGridColumns (grid) {
        // Ignore resizing request when grid was emptied while column widths are already available
        // This can happen when DataSource destroys data tree (e.g. ordering event) and to
        // prevent column collapse we just wait for table to be filled again
        if (grid.body.rows.length === 0 && grid.ui.columnsWidths.length > 0) return;

        calculateColumnWidths(grid);
        resizeCells(grid);
        resizeBreakdownRows(grid);
    }

    function getBreakdownColumnStyle (grid, row) {
        var paddingLeft = (row.level - 1) * zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
        // Indent breakdown rows on last level with additional padding because no collapse icon is shown in these rows
        var breakdownLevel = grid.meta.dataService.getBreakdownLevel();
        if (breakdownLevel > 1 && breakdownLevel === row.level) {
            paddingLeft += zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
        }

        return {
            'padding-left': paddingLeft + 'px',
        };
    }

    function getFieldGoalStatusClass (status) {
        switch (status) {
        case constants.emoticon.HAPPY: return 'superperforming-goal';
        case constants.emoticon.SAD: return 'underperforming-goal';
        default: return '';
        }
    }

    return {
        requestAnimationFrame: requestAnimationFrame,
        resizeGridColumns: resizeGridColumns,
        getBreakdownColumnStyle: getBreakdownColumnStyle,
        getFieldGoalStatusClass: getFieldGoalStatusClass,
    };
}]);
