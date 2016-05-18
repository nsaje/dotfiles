/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridUIService', ['zemGridConstants', function (zemGridConstants) {

    function calculateColumnsWidths (grid, element) {
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
        });
    }

    function resizeCells (grid, element) {
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

    function resizeGridColumns (grid) {
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
    }

    function getRowClass (grid, row) {
        var classes = [];
        classes.push('level-' + row.level);

        if (row.level === grid.meta.levels) {
            classes.push('level-last');
        }

        if (row.type === zemGridConstants.gridRowType.BREAKDOWN) {
            classes.push('breakdown');
        }
        return classes;
    }

    return {
        resizeGridColumns: resizeGridColumns,
        getRowClass: getRowClass,
    };
}]);
