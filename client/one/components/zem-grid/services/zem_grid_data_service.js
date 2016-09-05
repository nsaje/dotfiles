/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridDataService', ['$q', 'zemGridParser', function ($q, zemGridParser) { // eslint-disable-line max-len

    // GridDataService is responsible to request data from DataSource and listen to any DataSource changes
    // It prepares data suitable for Grid component along with data states (initializing, loading, etc.) used
    // to communicate current data source status

    function GridDataService (grid, dataSource) {
        // Last notification cached to close it when new arrives (e.g. saving data)
        var lastNotification = null;

        //
        // Public API
        //
        this.initialize = initialize;
        this.loadData = loadData;
        this.saveData = saveData;

        this.isSaveRequestInProgress = dataSource.isSaveRequestInProgress;

        this.DS_FILTER = dataSource.FILTER;
        this.setBreakdown = dataSource.setBreakdown;
        this.getBreakdown = dataSource.getBreakdown;
        this.getBreakdownLevel = dataSource.getBreakdownLevel;
        this.setOrder = dataSource.setOrder;
        this.getOrder = dataSource.getOrder;
        this.setDateRange = dataSource.setDateRange;
        this.getDateRange = dataSource.getDateRange;
        this.setFilter = dataSource.setFilter;
        this.getFilter = dataSource.getFilter;


        function initialize () {
            dataSource.onStatsUpdated(grid.meta.scope, handleSourceStatsUpdate);
            dataSource.onDataUpdated(grid.meta.scope, handleSourceDataUpdate);
            loadMetaData().then(function () {
                grid.meta.initialized = true;
                loadData().then(function () {
                    // Workaround - goals are defined after initial data is loaded; therefor reload metadata
                    loadMetaData();
                });
            });
        }

        function loadMetaData () {
            var deferred = $q.defer();
            dataSource.getMetaData(true).then(
                function (data) {
                    zemGridParser.parseMetaData(grid, data);
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
            dataSource.getData(breakdown, size).then(
                function () {
                    // Data is already been processed
                    // on source data update event
                    deferred.resolve();
                },
                function (err) {
                    // TODO: Handle errors
                    grid.meta.loading = false;
                    deferred.reject(err);
                }
            );
            return deferred.promise;
        }

        function saveData (value, row, column) {
            var deferred = $q.defer();
            dataSource.saveData(value, row.data, column.data).then(function (data) {
                if (data.notification) {
                    if (lastNotification) lastNotification.close();
                    lastNotification = grid.meta.api.notify(data.notification.type, data.notification.msg, true);
                }
                deferred.resolve(data);
            }, function (err) {
                deferred.reject(err);
            });
            return deferred.promise;
        }

        function handleSourceStatsUpdate () {
            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
        }

        function handleSourceDataUpdate (event, data) {
            zemGridParser.parse(grid, data);
            grid.meta.loading = !data.breakdown;
            grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
        }
    }

    return {
        createInstance: function (grid, dataSource) {
            return new GridDataService(grid, dataSource);
        },
    };
}]);
