/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridColumnsService', ['zemGridConstants', 'zemGridStorageService', function (zemGridConstants, zemGridStorageService) { // eslint-disable-line max-len

    function ColumnsService (grid) {
        var pubsub = grid.meta.pubsub;

        initialize();

        //
        // Public API
        //
        this.setVisibleColumns = setVisibleColumns;
        this.getVisibleColumns = getVisibleColumns;
        this.isColumnVisible = isColumnVisible;
        this.setColumnVisibility = setColumnVisibility;

        function initialize () {
            pubsub.register(pubsub.EVENTS.METADATA_UPDATED, null, initializeColumns);
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, null, initializeColumnsState);
        }

        function initializeColumns () {
            zemGridStorageService.loadColumns(grid);
            initializeColumnsState();
        }

        function initializeColumnsState () {
            var breakdowns = grid.meta.dataService.getBreakdown().map(function (breakdown) { return breakdown.query; });
            grid.header.columns.forEach(function (column) {
                column.disabled = !isColumnAvailable(column, grid.meta.data.level, breakdowns);
            });
            pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
        }

        function isColumnAvailable (column, level, breakdowns) {
            if (!column.data.exceptions) {
                return true;
            }

            if (column.data.exceptions.custom) {
                for (var i = 0; i < column.data.exceptions.custom.length; ++i) {
                    var customException = column.data.exceptions.custom[i];
                    if (customException.level === level && customException.breakdown === breakdowns[0]) {
                        return customException.shown;
                    }
                }
            }

            if (column.data.exceptions.breakdowns) {
                return intersects(column.data.exceptions.breakdowns, breakdowns);
            }

            return true;
        }

        function intersects (array1, array2) {
            // Simple solution for finding if arrays are having common element
            return array1.filter(function (n) {
                return array2.indexOf(n) != -1;
            }).length > 0;
        }

        function getVisibleColumns () {
            var visibleColumns = grid.header.columns.filter(function (column) {
                return column.visible && !column.disabled;
            });

            // Add grid-only (non-data) columns
            if (grid.meta.options.selection && grid.meta.options.selection.enabled) {
                visibleColumns.unshift({type: zemGridConstants.gridColumnTypes.CHECKBOX});
            }
            return visibleColumns;
        }

        function setVisibleColumns (columns, visible) {
            if (!Array.isArray(columns)) columns = [columns];

            columns.forEach(function (column) {
                column.visible = visible;
            });
            zemGridStorageService.saveColumns(grid);
            pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
        }

        function isColumnVisible (column) {
            return column.visible;
        }

        function setColumnVisibility (column, visible) {
            column.visible = visible;
            zemGridStorageService.saveColumns(grid);
            pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
        }
    }

    return {
        createInstance: function (grid) {
            return new ColumnsService(grid);
        }
    };
}]);
