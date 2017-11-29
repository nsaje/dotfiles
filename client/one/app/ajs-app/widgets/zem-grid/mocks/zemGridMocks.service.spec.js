angular.module('one.widgets').service('zemGridMocks', function ($q, zemGridEndpointService) { // eslint-disable-line max-len

    this.createMetaData = createMetaData;
    this.createApi = createApi;

    function createMetaData (level, breakdown) {
        return zemGridEndpointService.createMetaData(level, -1, breakdown);
    }

    function createApi (level, breakdown) {
        var metaData = createMetaData(level, breakdown);

        var api = {
            hasPermission: function () { return true; },
            isPermissionInternal: function () { return false; },

            isInitialized: function () { return true; },
            getMetaData: function () { return metaData; },
            getRows: function () { return []; },
            getColumns: function () { return []; },
            getBareBoneCategories: function () { return []; },
            getCategorizedColumns: function () { return []; },

            loadData: fnWithPromise,
            loadMetaData: fnWithPromise,
            setBreakdown: angular.noop,
            getBreakdown: angular.noop,
            getBreakdownLevel: angular.noop,
            setOrder: angular.noop,
            getOrder: angular.noop,
            setFilter: angular.noop,
            getFilter: angular.noop,

            // Selection service API
            getSelection: angular.noop,
            clearSelection: angular.noop,
            setSelection: angular.noop,
            getSelectionOptions: angular.noop,
            setSelectionOptions: angular.noop,

            // Columns service API
            setVisibleColumns: angular.noop,
            getVisibleColumns: angular.noop,
            getCostMode: angular.noop,
            setCostMode: angular.noop,

            // Listeners - pubsub rewiring
            onMetaDataUpdated: angular.noop,
            onDataUpdated: angular.noop,
            onColumnsUpdated: angular.noop,
            onSelectionUpdated: angular.noop,
        };

        initializeApiColumns(api);

        return api;
    }

    function initializeApiColumns (api) {
        api.getColumns = function () {
            return api.getMetaData().columns.map(function (col) {
                return {
                    type: col.type,    // Reuse data type - type of column (text, link, icon, etc.)
                    field: col.field,  // Reuse data field - some kind of id  (data retrieval, storage, etc.)
                    data: col,         // Column meta-data retrieved from endpoint
                    visible: true,     // Visibility flag
                };
            });
        };
    }

    function fnWithPromise () {
        return $q.resolve();
    }
});
