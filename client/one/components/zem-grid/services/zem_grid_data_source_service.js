/* globals oneApp */
'use strict';

oneApp.factory('zemGridDataService', ['$q', 'zemGridParser', 'zemGridUIService', function ($q, zemGridParser, zemGridUIService) { // eslint-disable-line max-len

    // GridDataService is responsible to request data from DataSource and listen to any DataSource changes
    // It prepares data suitable for Grid component along with data states (initializing, loading, etc.) used
    // to communicate current data source status

    function GridDataService (grid) {

        //
        // Public API
        //
        this.initialize = initialize;
        this.loadMetaData = loadMetaData;
        this.loadData = loadData;


        function initialize () {
            grid.meta.source.onDataUpdated(grid.meta.scope, handleSourceDataUpdate);
            loadMetaData().then(function () {
                grid.meta.initialized = true;
                loadData();
            });
        }

        function loadMetaData () {
            var deferred = $q.defer();
            grid.meta.source.getMetaData().then(
                function (data) {
                    grid.header.columns = data.columns;
                    grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);
                    deferred.resolve();
                }
            );
            return deferred.promise;
        }

        function loadData (row, size) {
            var breakdown;
            if (row) {
                // When additional data (load more...) is requested
                // breakdown row is passed as an argument
                breakdown = row.data;
            }
            var deferred = $q.defer();
            grid.meta.source.getData(breakdown, size).then(
                function (data) {
                    zemGridParser.parse(grid, data);
                    deferred.resolve();
                },
                function () {
                    // TODO: Handle errors
                }
            );
            return deferred.promise;
        }

        function handleSourceDataUpdate (event, data) {
            zemGridParser.parse(grid, data);
            zemGridUIService.resetUIState(grid);
            grid.meta.loading = !data.breakdown;
            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
        }
    }

    return {
        createInstance: function (grid) {
            return new GridDataService(grid);
        },
    };
}]);
