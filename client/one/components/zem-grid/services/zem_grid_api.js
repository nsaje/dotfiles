/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridApi', ['$rootScope', 'zemGridStorageService', function ($rootScope, zemGridStorageService) { // eslint-disable-line max-len

    //
    // GridApi provides interface for interaction with zem-grid
    // Reference can be sent to non-grid components (e.g. zem-grid-column-selector, zem-grid-breakdown-selector),
    // or may be passed back to calling controller to enable interaction between them.
    //

    function GridApi (grid) {
        var pubsub = grid.meta.pubsub;

        // Grid Object API
        this.isInitialized = isInitialized;
        this.getMetaData = getMetaData;
        this.getRows = getRows;
        this.getColumns = getColumns;

        // Data service API
        this.DS_FILTER = grid.meta.dataService.DS_FILTER;
        this.loadData = grid.meta.dataService.loadData;
        this.loadMetaData = grid.meta.dataService.loadMetaData;
        this.setBreakdown = grid.meta.dataService.setBreakdown;
        this.getBreakdown = grid.meta.dataService.getBreakdown;
        this.getBreakdownLevel = grid.meta.dataService.getBreakdownLevel;
        this.setOrder = grid.meta.dataService.setOrder;
        this.getOrder = grid.meta.dataService.getOrder;
        this.setDateRange = grid.meta.dataService.setDateRange;
        this.getDateRange = grid.meta.dataService.getDateRange;
        this.setFilter = grid.meta.dataService.setFilter;
        this.getFilter = grid.meta.dataService.getFilter;

        // Selection service API
        this.getSelection = grid.meta.selectionService.getSelection;
        this.clearSelection = grid.meta.selectionService.clearSelection;
        this.setSelection = grid.meta.selectionService.setSelection;
        this.getSelectionOptions = grid.meta.selectionService.getConfig;
        this.setSelectionOptions = grid.meta.selectionService.setConfig;

        // Columns service API
        this.setVisibleColumns = grid.meta.columnsService.setVisibleColumns;
        this.getVisibleColumns = grid.meta.columnsService.getVisibleColumns;

        // Notifications service API
        this.notify = grid.meta.notificationService.notify;

        // Listeners - pubsub rewiring
        this.onMetaDataUpdated = onMetaDataUpdated;
        this.onDataUpdated = onDataUpdated;
        this.onColumnsUpdated = onColumnsUpdated;
        this.onSelectionUpdated = onSelectionUpdated;

        function isInitialized () {
            return grid.meta.initialized;
        }

        function getMetaData () {
            return grid.meta.data;
        }

        function getRows () {
            var rows = grid.body.rows.slice();
            if (grid.footer.row) {
                rows.push(grid.footer.row);
            }
            return rows;
        }

        function getColumns () {
            return grid.header.columns;
        }

        function onMetaDataUpdated (scope, callback) {
            registerListener(pubsub.EVENTS.METADATA_UPDATED, scope, callback);
        }

        function onDataUpdated (scope, callback) {
            registerListener(pubsub.EVENTS.DATA_UPDATED, scope, callback);
        }

        function onColumnsUpdated (scope, callback) {
            registerListener(pubsub.EVENTS.EXT_COLUMNS_UPDATED, scope, callback);
        }

        function onSelectionUpdated (scope, callback) {
            registerListener(pubsub.EVENTS.EXT_SELECTION_UPDATED, scope, callback);
        }

        function registerListener (event, scope, callback) {
            pubsub.register(event, scope, callback);
        }
    }

    return {
        createInstance: function (grid) {
            return new GridApi(grid);
        },
    };
}]);
