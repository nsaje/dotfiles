/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCopy', ['$timeout', 'zemGridConstants', 'zemGridDataFormatter', function ($timeout, zemGridConstants, zemGridDataFormatter) {
    return {
        restrict: 'A',
        link: function (scope, element) {
            var grid = scope.ctrl.grid;
            element.on('copy', handleCopy);

            function handleCopy () {
                var selection = window.getSelection();
                // If only one element is selected leave default behaviour
                if (selection.anchorNode === selection.extentNode) return;

                // Find all rows between selected elements including header footer
                // export them and apply new text to copy selection
                var anchorElement = angular.element(selection.anchorNode);
                var extentElement = angular.element(selection.extentNode);

                var from = getExportIndex(anchorElement);
                var to = getExportIndex(extentElement);
                if (from > to) {
                    var temp = from;
                    from = to;
                    to = temp;
                }

                var text = exportGrid(grid, from, to);
                applyTextToSelection(selection, text);
            }

            function getExportIndex (element) {
                var idx;
                if (element.closest('.zem-grid-header').length > 0) {
                    idx = -1; // Special case - Include header
                } else if (element.closest('.zem-grid-footer').length > 0) {
                    idx = Number.MAX_VALUE; // Special case - Include footer
                } else {
                    var posTop = element.closest('.zem-grid-row').position().top;
                    idx = Math.floor(posTop / zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                }
                return idx;
            }

            function exportGrid (grid, from, to) {
                // Export all rows between from and to
                // Special case
                //      from<0: include header and all row until to
                //      to > #rows: include footer and all rows starting with from
                var exportColumns = getExportColumns(grid);
                var exportText = '';

                // Header
                if (from < 0) {
                    exportText += exportHeader(exportColumns) + '<br>';
                    from = 0;
                }

                // Body - rows [from, to]
                for (var idx = from; idx <= Math.min(to, grid.body.rows.length - 1); ++idx) {
                    var row = grid.body.rows[idx];
                    if (row.type === zemGridConstants.gridRowType.BREAKDOWN) continue;
                    exportText += exportRow(exportColumns, row) + '<br>';
                }

                // Footer
                if (to === Number.MAX_VALUE) {
                    exportText += exportRow(exportColumns, grid.footer.row) + '<br>';
                }
                return exportText;
            }

            function getExportColumns (grid) {
                return grid.header.visibleColumns.filter(function (column) {
                    return zemGridConstants.gridColumnTypes.EXPORT_TYPES.indexOf(column.type) >= 0;
                });
            }

            function exportHeader (columns) {
                return columns.map(function (column) {
                    if (!column.data) return undefined;
                    return column.data.name;
                }).join('\t');
            }

            function exportRow (columns, row) {
                return columns.map(function (column) {
                    if (!column.data || !column.data.name) return undefined;

                    if (row.level === zemGridConstants.gridRowLevel.FOOTER
                        && column.type === zemGridConstants.gridColumnTypes.BREAKDOWN) {
                        return 'TOTALS';
                    }
                    var stat = row.data.stats[column.field];
                    return exportStat(stat, column);
                }).join('\t');
            }

            function exportStat (stat, column) {
                if (!stat) return 'N/A';
                if (zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(column.type) >= 0) {
                    return zemGridDataFormatter.formatValue(stat.value, column);
                }
                return stat.value || stat.url || ' ';
            }

            function applyTextToSelection (selection, text) {
                // Create new element, apply text to it
                // and update selection to target this new element
                var newdiv = document.createElement('div');
                newdiv.style.position = 'absolute';
                newdiv.style.left = '-99999px';

                //insert the container, fill it with the extended text, and define the new selection
                document.body.appendChild(newdiv);
                newdiv.innerHTML = text;
                selection.selectAllChildren(newdiv);
                $timeout(function () {
                    document.body.removeChild(newdiv);
                }, 100);
            }
        }
    };
}]);
