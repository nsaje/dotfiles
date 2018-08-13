angular
    .module('one.widgets')
    .directive('zemGridCopy', function(
        $timeout,
        zemGridConstants,
        zemGridDataFormatter
    ) {
        return {
            restrict: 'A',
            link: function(scope, element) {
                var grid = scope.$ctrl.grid;
                element.on('copy', handleCopy);

                function handleCopy() {
                    var selection = window.getSelection();
                    // If only one element is selected leave default behaviour
                    if (selection.anchorNode === selection.extentNode) return;

                    // If selection is not within grid element leave default behaviour
                    if (grid.ui.element.has(selection.anchorNode).length === 0)
                        return;
                    if (grid.ui.element.has(selection.extentNode).length === 0)
                        return;

                    // Find all rows between selected elements including header footer
                    // export them as a html table and apply it to copy selection
                    var anchorElement = angular.element(selection.anchorNode);
                    var extentElement = angular.element(selection.extentNode);

                    var from = getExportIndex(anchorElement);
                    var to = getExportIndex(extentElement);
                    if (from === to) return;

                    if (from > to) {
                        var temp = from;
                        from = to;
                        to = temp;
                    }

                    var htmlTable = convertGridToTable(grid, from, to);
                    applyTableToSelection(selection, htmlTable);
                }

                function getExportIndex(element) {
                    var idx;
                    if (element.closest('.zem-grid-header').length > 0) {
                        idx = -1; // Special case - Include header
                    } else if (element.closest('.zem-grid-footer').length > 0) {
                        idx = Number.MAX_VALUE; // Special case - Include footer
                    } else {
                        var posTop = element.closest('.zem-grid-row').position()
                            .top;
                        idx = Math.floor(
                            posTop /
                                zemGridConstants.gridBodyRendering.ROW_HEIGHT
                        );
                    }
                    return idx;
                }

                function convertGridToTable(grid, from, to) {
                    // Export all rows between from and to as HTML table that will be used for selection
                    // Special case
                    //      from<0: include header and all row until to
                    //      to > #rows: include footer and all rows starting with from
                    var exportColumns = getExportColumns(grid);
                    var htmlTable = '';

                    // Header
                    if (from < 0) {
                        htmlTable += convertHeader(exportColumns);
                        from = 0;
                    }

                    // Body - rows [from, to]
                    for (
                        var idx = from;
                        idx <= Math.min(to, grid.body.rows.length - 1);
                        ++idx
                    ) {
                        var row = grid.body.rows[idx];
                        if (row.type === zemGridConstants.gridRowType.BREAKDOWN)
                            continue;
                        htmlTable += convertRow(exportColumns, row);
                    }

                    // Footer
                    if (to === Number.MAX_VALUE) {
                        htmlTable += convertRow(exportColumns, grid.footer.row);
                    }

                    return '<table>' + htmlTable + '</table>';
                }

                function getExportColumns(grid) {
                    return grid.header.visibleColumns.filter(function(column) {
                        return (
                            zemGridConstants.gridColumnTypes.EXPORT_TYPES.indexOf(
                                column.type
                            ) >= 0
                        );
                    });
                }

                function convertHeader(columns) {
                    var htmlTableHeader = columns
                        .map(function(column) {
                            if (!column.data) return undefined;
                            return column.data.name;
                        })
                        .join('</th><th>');
                    return '<tr><th>' + htmlTableHeader + '</th></tr>';
                }

                function convertRow(columns, row) {
                    if (!row) return '';

                    var htmlTableRow = columns
                        .map(function(column) {
                            if (!column.data || !column.data.name)
                                return undefined;

                            if (
                                row.level ===
                                    zemGridConstants.gridRowLevel.FOOTER &&
                                column.type ===
                                    zemGridConstants.gridColumnTypes.BREAKDOWN
                            ) {
                                return 'TOTALS';
                            }
                            var stat = row.data.stats[column.field];
                            return exportStat(stat, column);
                        })
                        .join('</td><td>');
                    return '<tr><td>' + htmlTableRow + '</td></tr>';
                }

                function exportStat(stat, column) {
                    if (!stat) return 'N/A';
                    if (
                        zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(
                            column.type
                        ) >= 0
                    ) {
                        var formatterOptions = angular.copy(column.data);
                        formatterOptions.currency = grid.meta.data.ext.currency;
                        return zemGridDataFormatter.formatValue(
                            stat.value,
                            formatterOptions
                        );
                    }
                    return stat.value || stat.url || ' ';
                }

                function applyTableToSelection(selection, htmlTable) {
                    // Create new element, apply text to it
                    // and update selection to target this new element
                    var div = document.createElement('div');
                    div.style.position = 'absolute';
                    div.style.left = '-99999px';

                    //insert the container, fill it with the extended text, and define the new selection
                    document.body.appendChild(div);
                    div.innerHTML = htmlTable;
                    selection.selectAllChildren(div);
                    $timeout(function() {
                        document.body.removeChild(div);
                    }, 100);
                }
            },
        };
    });
