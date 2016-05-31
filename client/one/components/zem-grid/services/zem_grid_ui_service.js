/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridUIService', ['$timeout', 'zemGridConstants', function ($timeout, zemGridConstants) {

    var requestAnimationFrame = (function () {
        return window.requestAnimationFrame       ||
               window.webkitRequestAnimationFrame ||
               window.mozRequestAnimationFrame    ||
               window.oRequestAnimationFrame      ||
               window.msRequestAnimationFrame     ||
               function (callback) {
                   window.setTimeout(callback, 1000 / 60);
               };
    })();

    function resetUIState (grid) {
        grid.ui.state.headerRendered = false;
        grid.ui.state.bodyRendered = false;
        grid.ui.state.footerRendered = false;
        grid.ui.state.columnsWidthsCalculated = false;
        grid.ui.columnsWidths = [];
    }

    function showLoader (grid, loading) {
        // TODO: Hide loader after gird rendering is done
        grid.ui.loading = loading;
    }

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
            var headerRendered = grid.ui.state.headerRendered,
                bodyRendered = grid.ui.state.bodyRendered,
                footerRendered = grid.ui.state.footerRendered;

            if (!grid.ui.state.columnsWidthsCalculated && headerRendered && bodyRendered && footerRendered) {
                // Adjust grid.ui.columnsWidths based on header columns widths
                calculateColumnsWidths(grid, grid.header.element);
                // Adjust grid.ui.columnsWidths based on body columns widths
                calculateColumnsWidths(grid, grid.body.element);
                // Adjust grid.ui.columnsWidths based on footer columns widths
                calculateColumnsWidths(grid, grid.footer.element);

                grid.ui.state.columnsWidthsCalculated = true;
            }

            if (grid.ui.state.columnsWidthsCalculated) {
                // Resize header columns based on grid.ui.columnsWidths
                resizeCells(grid, grid.header.element);
                // Resize body columns based on grid.ui.columnsWidths
                resizeCells(grid, grid.body.element);
                // Resize footer columns based on grid.ui.columnsWidths
                resizeCells(grid, grid.footer.element);
            }
        });
    }

    function getRowClass (grid, row) {
        var classes = [];
        classes.push('level-' + row.level);

        if (row.level === grid.meta.source.selectedBreakdown.length) {
            classes.push('level-last');
        }

        if (row.type === zemGridConstants.gridRowType.BREAKDOWN) {
            classes.push('breakdown');
        }
        return classes;
    }

    function setRowCollapsed (grid, gridRow, collapsed) {
        gridRow.collapsed = collapsed;
        var idx = grid.body.rows.indexOf(gridRow);
        while (++idx < grid.body.rows.length) {
            var child = grid.body.rows[idx];
            if (child.level <= gridRow.level) break;
            child.visible = !gridRow.collapsed && !child.parent.collapsed;
        }
    }

    function toggleCollapse (grid, gridRow) {
        setRowCollapsed(grid, gridRow, !gridRow.collapsed);
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
    }

    function toggleCollapseLevel (grid, level) {
        var collapsed = null;
        for (var i = 0; i < grid.body.rows.length; ++i) {
            var row = grid.body.rows[i];
            if (row.level === level) {
                if (collapsed === null)
                    collapsed = !row.collapsed;
                setRowCollapsed(grid, row, collapsed);
            }
        }
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
    }

    return {
        requestAnimationFrame: requestAnimationFrame,
        resetUIState: resetUIState,
        showLoader: showLoader,
        resizeGridColumns: resizeGridColumns,
        getRowClass: getRowClass,

        toggleCollapse: toggleCollapse,
        toggleCollapseLevel: toggleCollapseLevel,
    };
}]);
