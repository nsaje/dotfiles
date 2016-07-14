/* globals oneApp */
'use strict';

oneApp.factory('zemGridApi', ['$rootScope', 'zemGridStorageService', function ($rootScope, zemGridStorageService) { // eslint-disable-line max-len

    //
    // GridApi provides interface for interaction with zem-grid
    // Reference can be sent to non-grid components (e.g. zem-grid-column-selector, zem-grid-breakdown-selector),
    // or may be passed back to calling controller to enable interaction between them.
    //

    // Definition of events used internally in GridApi
    // External listeners are registered through dedicated methods
    var EVENTS = {
        COLUMNS_LOADED: 'zem-grid-api-columns-loaded',
        ROWS_LOADED: 'zem-grid-api-rows-loaded',
        ROWS_SELECTION_CHANGED: 'zem-grid-api-rows-selection-changed',
        ROWS_COLLAPSE_CHANGED: 'zem-grid-api-rows-collapse-changed',
        COLUMNS_VISIBILITY_CHANGED: 'zem-grid-api-columns-visibility-changed',
    };

    function GridApi (grid) {
        //
        // Public API
        //
        this.isInitialized = isInitialized;
        this.getMetaData = getMetaData;
        this.getDataService = getDataService;
        this.getRows = getRows;
        this.getColumns = getColumns;
        this.getVisibleColumns = getVisibleColumns;
        this.getSelectedRows = getSelectedRows;
        this.getVisibleRows = getVisibleRows;

        this.setCollapsedRows = setCollapsedRows;
        this.setCollapsedLevel = setCollapsedLevel;
        this.setSelectedRows = setSelectedRows;
        this.setVisibleColumns = setVisibleColumns;

        this.onRowsLoaded = onRowsLoaded;
        this.onColumnsLoaded = onColumnsLoaded;
        this.onRowsCollapseChanged = onRowsCollapseChanged;
        this.onRowsSelectionChanged = onRowsSelectionChanged;
        this.onColumnsVisibilityChanged = onColumnsVisibilityChanged;

        // Initialize API
        initialize();

        function initialize () {
            // Re-Wire some of pubsub events; notify when rows and columns are available
            grid.meta.pubsub.register(grid.meta.pubsub.EVENTS.DATA_UPDATED, function () {
                notifyListeners(EVENTS.ROWS_LOADED, getRows());
            });
            grid.meta.pubsub.register(grid.meta.pubsub.EVENTS.METADATA_UPDATED, function () {
                notifyListeners(EVENTS.COLUMNS_LOADED, getColumns());
            });
        }

        function setCollapsedRows (rows, collapsed) {
            if (!Array.isArray(rows)) rows = [rows];

            rows.forEach(function (row) {
                row.collapsed = collapsed;
                var idx = grid.body.rows.indexOf(row);
                while (++idx < grid.body.rows.length) {
                    var child = grid.body.rows[idx];
                    if (child.level <= row.level) break;
                    child.visible = !row.collapsed && !child.parent.collapsed;
                }
            });

            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            notifyListeners(EVENTS.ROWS_COLLAPSE_CHANGED, rows);
        }

        function setCollapsedLevel (level, collapsed) {
            var rows = grid.body.rows.filter(function (row) {
                return row.level === level;
            });
            setCollapsedRows(rows, collapsed);
        }

        function setSelectedRows (rows, selected) {
            if (!Array.isArray(rows)) rows = [rows];

            rows.forEach(function (row) {
                row.selected = selected;
            });

            notifyListeners(EVENTS.ROWS_SELECTION_CHANGED, rows);
        }

        function setVisibleColumns (columns, visible) {
            if (!Array.isArray(columns)) columns = [columns];

            columns.forEach(function (column) {
                column.visible = visible;
            });

            zemGridStorageService.saveColumns(grid);
            notifyListeners(EVENTS.COLUMNS_VISIBILITY_CHANGED, columns);
            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
        }

        function isInitialized () {
            return grid.meta.initialized;
        }

        function getMetaData () {
            return grid.meta.data;
        }

        function getDataService () {
            return grid.meta.service;
        }

        function getRows () {
            var rows = grid.body.rows.slice();
            if (grid.footer.row) {
                rows.push(grid.footer.row);
            }
            return rows;
        }

        function getSelectedRows () {
            var selectedData = [];
            grid.body.rows.forEach(function (row) {
                if (row.selected) {
                    selectedData.push(row);
                }
            });

            if (grid.footer.row && grid.footer.row.selected) {
                selectedData.push(grid.footer.row);
            }

            return selectedData;
        }

        function getVisibleRows () {
            return getRows().filter(function (row) {
                return row.visible;
            });
        }

        function getColumns () {
            return grid.header.columns;
        }

        function getVisibleColumns () {
            return grid.header.columns.filter(function (column) {
                return column.visible;
            });
        }

        function onColumnsLoaded (scope, callback) {
            registerListener(EVENTS.COLUMNS_LOADED, scope, callback);
        }

        function onRowsLoaded (scope, callback) {
            registerListener(EVENTS.ROWS_LOADED, scope, callback);
        }

        function onRowsSelectionChanged (scope, callback) {
            registerListener(EVENTS.ROWS_SELECTION_CHANGED, scope, callback);
        }

        function onRowsCollapseChanged (scope, callback) {
            registerListener(EVENTS.ROWS_COLLAPSE_CHANGED, scope, callback);
        }

        function onColumnsVisibilityChanged (scope, callback) {
            registerListener(EVENTS.COLUMNS_VISIBILITY_CHANGED, scope, callback);
        }

        function registerListener (event, scope, callback) {
            scope = scope || grid.meta.scope;
            var handler = $rootScope.$on(event, callback);
            scope.$on('$destroy', handler);
        }

        function notifyListeners (event, data) {
            $rootScope.$emit(event, data);
        }
    }

    return {
        createInstance: function (grid) {
            return new GridApi(grid);
        },
    };
}]);
