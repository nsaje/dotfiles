/* globals oneApp */
'use strict';

oneApp.factory('zemGridService', ['$q', 'zemGridParser', 'zemGridUIService', function ($q, zemGridParser, zemGridUIService) { // eslint-disable-line max-len

    function GridService (grid) {
        this.loadMetaData = loadMetaData;
        this.loadData = loadData;

        this.initialize = initialize;

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
            return new GridService(grid);
        },
    };
}]);
