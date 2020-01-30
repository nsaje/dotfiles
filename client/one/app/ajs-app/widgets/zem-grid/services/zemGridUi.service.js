var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .factory('zemGridUIService', function(
        $timeout,
        $state,
        zemGridConstants,
        zemGridDataFormatter,
        zemGridActionsService
    ) {
        // eslint-disable-line max-len
        var requestAnimationFrame = (function() {
            return (
                window.requestAnimationFrame ||
                window.webkitRequestAnimationFrame ||
                window.mozRequestAnimationFrame ||
                window.oRequestAnimationFrame ||
                window.msRequestAnimationFrame ||
                function(callback) {
                    window.setTimeout(callback, 1000 / 60);
                }
            );
        })();

        var headerElement = document.getElementById('zem-header');
        var filterSelectorElement = document.getElementById(
            'zem-filter-selector'
        );
        var headerBreadcrumbElement = document.getElementById(
            'zem-header-breadcrumb'
        );

        function calculateColumnWidths(grid) {
            // Calculate rendered column widths, based on grid contents,
            // and configured styles (font, min/max widths, padding, etc.)
            // Solution is sub-optimal, since it can only calculate text fields (including parsed values)
            var headerCells = grid.header.ui.element.find('.zem-grid-cell');

            var gridWidth = 0;
            var columnWidths = [];
            headerCells.each(function(i) {
                if (!grid.header.visibleColumns[i]) return;

                // Retrieve properties that affects column width
                var font = window
                    .getComputedStyle(headerCells[i], null)
                    .getPropertyValue('font');
                var padding = window
                    .getComputedStyle(headerCells[i], null)
                    .getPropertyValue('padding-left');
                var maxWidth = window
                    .getComputedStyle(headerCells[i], null)
                    .getPropertyValue('max-width');
                var minWidth = window
                    .getComputedStyle(headerCells[i], null)
                    .getPropertyValue('min-width');
                maxWidth =
                    parseInt(maxWidth) ||
                    zemGridConstants.gridStyle.DEFAULT_MAX_COLUMN_WIDTH;
                minWidth =
                    parseInt(minWidth) ||
                    zemGridConstants.gridStyle.DEFAULT_MIN_COLUMN_WIDTH;
                padding = parseInt(padding) || 0;

                // Calculate column column width without constraints (use only font)
                var width = calculateColumnWidth(
                    grid,
                    grid.header.visibleColumns[i],
                    font
                );

                // Apply constraints to column width (padding, max/min size)
                width += 2 * padding;
                if (
                    grid.header.visibleColumns[i].type !==
                    zemGridConstants.gridColumnTypes.ACTIONS
                ) {
                    width = Math.min(maxWidth, width);
                }
                width = Math.max(minWidth, width);

                columnWidths[i] = width;
                gridWidth += width;
            });

            var headerWidth = grid.header.ui.element[0].offsetWidth;
            if (
                grid.body.rows.length >
                zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE
            ) {
                // Check if scroller will be present and incorporate this into header width
                headerWidth -=
                    zemGridConstants.gridStyle.DEFAULT_SCROLLER_WIDTH;
            }
            var expandableColumnIndex = getVisibleColumnIndex(
                grid.header.visibleColumns,
                'breakdown_name'
            );
            resizeExpandableColumn(
                columnWidths,
                headerWidth,
                expandableColumnIndex
            );
            gridWidth = Math.max(headerWidth, gridWidth);

            grid.ui.columnsWidths = columnWidths;
            grid.ui.width = gridWidth;
            grid.ui.headerWidth = headerWidth;
        }

        function calculateColumnWidth(grid, column, font) {
            if (!column || !column.data) return -1;

            var width = getTextWidth(column.data.name, font);

            // Add breakdown by structure text width if displayed
            if (column.data.breakdownByStructureText) {
                width += getTextWidth(
                    column.data.breakdownByStructureText,
                    font
                );
            }

            width = Math.max(
                width,
                zemGridConstants.gridStyle.DEFAULT_ICON_SIZE
            ); // Column without text (e.g. only icon)
            if (column.data.internal) {
                width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
            }
            if (column.data.help) {
                width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
            }
            if (column.order !== zemGridConstants.gridColumnOrder.NONE) {
                width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
            }
            if (column.type === zemGridConstants.gridColumnTypes.EDIT_BUTTON) {
                width += zemGridConstants.gridStyle.DEFAULT_ICON_SIZE;
            }

            grid.body.rows.forEach(function(row) {
                if (row.type === zemGridConstants.gridRowType.BREAKDOWN) return;
                var data = row.data.stats[column.field];
                if (!data) return;

                // Format data to string and predict width based on it
                var formatterOptions = angular.copy(column.data);
                formatterOptions.currency = grid.meta.data.ext.currency;
                var formattedValue = zemGridDataFormatter.formatValue(
                    data.value || data.text,
                    formatterOptions
                );
                var valueWidth = getTextWidth(formattedValue, font);
                if (
                    column.type === zemGridConstants.gridColumnTypes.BREAKDOWN
                ) {
                    // Special case for breakdown column - add padding based on row level
                    valueWidth +=
                        (row.level - 1) *
                        zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
                    if (row.inGroup)
                        valueWidth +=
                            zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
                    // Add additional padding when collapse icon is shown
                    if (
                        grid.meta.dataService.getBreakdownLevel() > 1 &&
                        row.level > 0
                    ) {
                        valueWidth +=
                            zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
                    }
                } else if (
                    column.type === zemGridConstants.gridColumnTypes.ACTIONS
                ) {
                    valueWidth = zemGridActionsService.getWidth(
                        grid.meta.data.level,
                        grid.meta.data.breakdown,
                        row
                    );
                }
                width = Math.max(width, valueWidth);
            });

            if (grid.footer.row) {
                var data = grid.footer.row.data.stats[column.field];
                if (data) {
                    var formatterOptions = angular.copy(column.data);
                    formatterOptions.currency = grid.meta.data.ext.currency;
                    var formattedValue = zemGridDataFormatter.formatValue(
                        data.value,
                        formatterOptions
                    );
                    var valueWidth = getTextWidth(formattedValue, font);
                    width = Math.max(width, valueWidth);
                }
            }

            return width;
        }

        function getVisibleColumnIndex(visibleColumns, columnField) {
            for (var i = 0; i < visibleColumns.length; i++) {
                if (visibleColumns[i].field === columnField) {
                    return i;
                }
            }
            return visibleColumns.length - 1;
        }

        function resizeExpandableColumn(
            columnWidths,
            headerWidth,
            expandableColumnIndex
        ) {
            // Resize expandable column to make grid at least as wide as the viewport
            var computedColumnsWidth = 0;
            columnWidths.forEach(function(w) {
                computedColumnsWidth += w;
            });
            if (headerWidth > computedColumnsWidth) {
                columnWidths[expandableColumnIndex] +=
                    headerWidth - computedColumnsWidth;
            }
        }

        function getTextWidth(text, font) {
            if (typeof text !== 'string') return -1;
            if (!getTextWidth.canvas) {
                getTextWidth.canvas = document.createElement('canvas');
            }
            var context = getTextWidth.canvas.getContext('2d');
            context.font = font;
            var metrics = context.measureText(text);
            return metrics.width;
        }

        function resizeCells(grid) {
            var element = grid.ui.element;
            var rows = element.find('.zem-grid-row');
            rows.each(function(rowIndex, row) {
                row = angular.element(row);
                var cells = row.find('.zem-grid-cell');
                cells.each(function(cellIndex, cell) {
                    angular.element(cell).css({
                        width: grid.ui.columnsWidths[cellIndex] + 'px',
                    });
                });
            });
        }

        function resizeBreakdownRows(grid) {
            // Resize breakdown columns based on breakdown column position
            // Breakdown split widths - before breakdown (empty), breakdown (pagination), after breakdown (load-more)
            var element = grid.ui.element;
            var breakdownSplitWidths = [0];
            grid.header.visibleColumns.forEach(function(column, idx) {
                if (
                    column.type === zemGridConstants.gridColumnTypes.BREAKDOWN
                ) {
                    breakdownSplitWidths.push(grid.ui.columnsWidths[idx]);
                    breakdownSplitWidths.push(0);
                    return;
                }
                breakdownSplitWidths[breakdownSplitWidths.length - 1] +=
                    grid.ui.columnsWidths[idx];
            });

            var paginationCellPadding =
                breakdownSplitWidths[0] +
                zemGridConstants.gridStyle.CELL_PADDING;
            var paginationCellWidth =
                breakdownSplitWidths[0] + breakdownSplitWidths[1];
            var loadMoreCellWidth = grid.ui.headerWidth - paginationCellWidth;
            if (breakdownSplitWidths.length === 1) {
                // Fallback if BREAKDOWN column has not been found
                paginationCellPadding = 50;
                paginationCellWidth = 200;
                loadMoreCellWidth = grid.ui.headerWidth - 250;
            }

            element.find('.breakdown-row-primary-cell').css({
                width: paginationCellWidth + 'px',
                'max-width': paginationCellWidth + 'px',
                'padding-left': paginationCellPadding + 'px',
            });

            element.find('.breakdown-row-info-cell').css({
                width: loadMoreCellWidth + 'px',
                'max-width': loadMoreCellWidth + 'px',
            });
        }

        function initializePivotColumns(grid) {
            // Prepare styles for pivot columns (e.g. absolute position, z-index)
            // Set correct margin to the first non-pivot column (pivot columns are absolutely positioned)
            var left = 0;
            for (var idx = 0; idx < grid.header.visibleColumns.length; ++idx) {
                var column = grid.header.visibleColumns[idx];
                // Lift columns to overlay fixed ones. Additionally, Checkbox columns should be placed to
                // highest zIndex so that dropdown menu covers all other pivot columns
                var zIndex =
                    column.type === zemGridConstants.gridColumnTypes.CHECKBOX
                        ? 100
                        : 10;
                column.style = {
                    'z-index': zIndex,
                    position: 'absolute',
                };
                column.left = left; // cache correct position for later use
                left += grid.ui.columnsWidths[idx];
                column.pivot = true;

                if (
                    column.type === zemGridConstants.gridColumnTypes.BREAKDOWN
                ) {
                    if (idx + 1 < grid.header.visibleColumns.length) {
                        grid.header.visibleColumns[idx + 1].style = {
                            'margin-left': left + 'px',
                        };
                    }
                    grid.ui.pivotColumnsWidth = left;
                    break;
                }
            }
            updatePivotColumns(grid, grid.body.ui.scrolleft || 0);
        }

        function updatePivotColumns(grid, leftOffset, animate) {
            if (!grid.body.ui.element) return;
            if (grid.ui.element.is(':hidden')) return;

            grid.header.ui.element
                .find('.zem-grid-header-cell')
                .each(updateCell);
            grid.footer.ui.element
                .find('.zem-grid-row > .zem-grid-cell')
                .each(updateCell);
            grid.body.ui.element
                .find('.zem-grid-row-breakdown')
                .each(updateBreakdownRow);
            grid.body.ui.element.find('.zem-grid-row').each(function(idx, row) {
                angular
                    .element(row)
                    .find('.zem-grid-cell')
                    .each(updateCell);
            });

            function updateBreakdownRow(idx, _row) {
                // Fix entire breakdown row
                var row = angular.element(_row);
                var style = getTranslateStyle(leftOffset);
                style.position = 'absolute';
                row.css(style);
                // Add style to primary cell to be consistent with data rows/cells
                row.find('.breakdown-row-primary-cell').css(
                    getBreakdownColumnStyle(leftOffset)
                );
            }

            function updateCell(idx, _cell) {
                var cell = angular.element(_cell);
                var column = grid.header.visibleColumns[idx];
                if (column) cell.css(getColumnStyle(column));
            }

            function getColumnStyle(column) {
                var style = column.style || {};
                if (!column.pivot) return style;

                style = getTranslateStyle(leftOffset + column.left);
                angular.extend(style, column.style);

                if (
                    column.type === zemGridConstants.gridColumnTypes.BREAKDOWN
                ) {
                    angular.extend(style, getBreakdownColumnStyle(leftOffset));
                }
                return style;
            }

            function getTranslateStyle(left) {
                var translateCssProperty = 'translateX(' + left + 'px)';
                var style = {
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    transform: translateCssProperty,
                    transition: 'none',
                };

                if (animate) {
                    style.transition = 'transform 50ms ease-out';
                }
                return style;
            }

            function getBreakdownColumnStyle(leftOffset) {
                // TODO: this will probably change in the future - create util functions/styles
                // fade right border to show pivot column break when h-scrolled
                var style = {};
                var borderStyle = 'solid 1px rgba(63, 84, 127, 0.2)';
                style['border-right'] = leftOffset ? borderStyle : '';
                return style;
            }
        }

        function resizeGridColumns(grid) {
            if (!grid.ui.element) return;
            if (grid.ui.element.is(':hidden')) return;

            clearColumnStyles(grid);
            calculateColumnWidths(grid);
            resizeCells(grid);
            resizeBreakdownRows(grid);
            initializePivotColumns(grid);
        }

        function clearColumnStyles(grid) {
            if (!grid.body.ui.element) return;

            grid.header.visibleColumns.forEach(function(column) {
                column.left = 0;
                column.pivot = false;
                column.style = {};
            });

            grid.header.ui.element
                .find('.zem-grid-header-cell')
                .each(clearStyle);
            grid.body.ui.element.find('.zem-grid-cell').each(clearStyle);
            grid.footer.ui.element.find('.zem-grid-cell').each(clearStyle);

            function clearStyle(idx, _cell) {
                var cell = angular.element(_cell);
                cell.removeAttr('style');
            }
        }

        function getBreakdownColumnStyle(grid, row) {
            var paddingLeft =
                (row.level - 1) *
                zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
            if (row.inGroup)
                paddingLeft +=
                    zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;

            // Indent breakdown rows on last level with additional padding because no collapse icon is shown in these rows
            var breakdownLevel = grid.meta.dataService.getBreakdownLevel();
            if (breakdownLevel > 1 && breakdownLevel === row.level) {
                paddingLeft +=
                    zemGridConstants.gridStyle.BREAKDOWN_CELL_PADDING;
            }

            return {
                'padding-left': paddingLeft + 'px',
            };
        }

        function getFieldGoalStatusClass(status) {
            switch (status) {
                case constants.emoticon.HAPPY:
                    return 'superperforming-goal';
                case constants.emoticon.SAD:
                    return 'underperforming-goal';
                default:
                    return '';
            }
        }

        function updateStickyElements(grid) {
            if (grid.ui.element.is(':hidden')) return;

            var SCROLL_BAR_WIDTH = 15;
            var MIN_VISIBLE_GRID_HEIGHT_NEEDED_TO_SHOW_STICKY_FOOTER =
                2 * zemGridConstants.gridBodyRendering.ROW_HEIGHT;
            var windowHeight = document.documentElement.clientHeight;
            var gridOffset = grid.ui.element.offset();
            var viewportBottom = windowHeight + window.pageYOffset;
            var spaceInViewportAvailableForGrid =
                viewportBottom - gridOffset.top;

            updateStickyHeaderPosition();
            updateStickyFooterPosition();
            updateStickyScroller();

            function updateStickyHeaderPosition() {
                var stickyHeader = grid.ui.element.find(
                    '.zem-grid-sticky__header'
                );
                stickyHeader.css(getHeaderStyle());
            }

            function updateStickyFooterPosition() {
                var stickyFooter = grid.ui.element.find(
                    '.zem-grid-sticky__footer'
                );
                stickyFooter.css(getFooterStyle());
            }

            function updateStickyScroller() {
                var isVisible = isFooterSticky();
                var scrollContainer = grid.ui.element.find(
                    '.zem-grid-sticky__scroller-container'
                );
                if (isVisible === scrollContainer.is(':visible')) return;

                if (isVisible) {
                    scrollContainer.show();
                    scrollContainer
                        .find('.zem-grid-sticky__scroller-content')
                        .width(grid.ui.width);
                    scrollContainer.scrollLeft(grid.body.ui.scrollLeft);
                } else {
                    scrollContainer.hide();
                }
            }

            function getHeaderStyle() {
                var contentTopOffset = getContentTopOffset();
                var style = {
                    position: 'static',
                    width: grid.ui.element.width() + 'px',
                };
                var isSticky =
                    window.pageYOffset + contentTopOffset > gridOffset.top;
                if (isSticky) {
                    style.position = 'fixed';
                    style.top = contentTopOffset + 'px';
                }
                return style;
            }

            function getFooterStyle() {
                var style = {
                    position: 'static',
                    width: grid.ui.element.width() + 'px',
                };
                if (isFooterSticky()) {
                    var stickyFooterHeight =
                        zemGridConstants.gridBodyRendering.ROW_HEIGHT +
                        SCROLL_BAR_WIDTH;
                    var spaceInViewportAvailableForStickyFooter =
                        spaceInViewportAvailableForGrid -
                        MIN_VISIBLE_GRID_HEIGHT_NEEDED_TO_SHOW_STICKY_FOOTER;

                    var bottom =
                        spaceInViewportAvailableForStickyFooter -
                        stickyFooterHeight;
                    bottom = Math.min(0, bottom);

                    style.position = 'fixed';
                    style.bottom = bottom + 'px';
                }
                return style;
            }

            function getContentTopOffset() {
                var offset = 0;

                offset += commonHelpers.isDefined(headerElement)
                    ? headerElement.offsetHeight
                    : 0;
                offset += commonHelpers.isDefined(filterSelectorElement)
                    ? filterSelectorElement.offsetHeight
                    : 0;

                if (window.matchMedia('(max-width: 1024px)').matches) {
                    offset += commonHelpers.isDefined(headerBreadcrumbElement)
                        ? headerBreadcrumbElement.offsetHeight
                        : 0;
                }

                return offset;
            }

            function isFooterSticky() {
                return (
                    spaceInViewportAvailableForGrid <
                        grid.ui.element.height() &&
                    spaceInViewportAvailableForGrid >=
                        MIN_VISIBLE_GRID_HEIGHT_NEEDED_TO_SHOW_STICKY_FOOTER
                );
            }
        }

        return {
            requestAnimationFrame: requestAnimationFrame,
            resizeGridColumns: resizeGridColumns,
            updatePivotColumns: updatePivotColumns,
            updateStickyElements: updateStickyElements,
            getBreakdownColumnStyle: getBreakdownColumnStyle,
            getFieldGoalStatusClass: getFieldGoalStatusClass,
        };
    });
