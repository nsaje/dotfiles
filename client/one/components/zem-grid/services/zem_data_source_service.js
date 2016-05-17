/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    var EVENTS = {
        ON_LOAD: 'zem-data-source-on-load',
    };

    //
    // DataRow
    //   --> Data (dict - key:value)
    //   --> Breakdown (optional)
    //      --> breakdown_id (request id)
    //      --> pagination (offset, size, count)
    //      --> rows [DataRow]
    //

    // this.data = DataRow
    //   --> Data (totals)
    //   --> Breakdown (L0/Base breakdown)
    //      --> breakdown_id = None
    //      --> pagination
    //      --> rows [DataRow]
    //

    //
    // ApiRow
    //   --> pagination
    //   --> breakdown_id
    //   --> rows [Data, ...]
    //
    //

    //
    // ApiRow -> DataRow
    //   Data -> DataRow (Data) w/ empty breakdown (breakdown_id, pagination = None/?)
    //

    // request by ids (level)

    function DataSource (endpoint) {
        var ds = this;

        this.dataRows =
        this.data = null;

        this.endpoint = endpoint;
        this.availableBreakdowns = endpoint.availableBreakdowns;
        this.selectedBreakdown = endpoint.defaultBreakdown;

        this.getData = getData;
        this.getMetaData = getMetaData;

        this.onLoad = onLoad;

        function applyBreakdown (breakdown) {
            if (breakdown.level === 0) {
                ds.data = breakdown.rows[0];
                return;
            }

            var position = breakdown.position;
            var current = ds.data.breakdown;
            for (var i = 1; i < breakdown.level; ++i) {
                current = current.rows[position[i]].breakdown;
            }

            current.rows = current.rows.concat(breakdown.rows);
            current.pagination.to = breakdown.pagination.to;
            current.pagination.size += breakdown.pagination.size;
        }

        function getMetaData () {
            var config = {
                selectedBreakdown: ds.selectedBreakdown,
            };
            return ds.endpoint.getMetaData(config);
        }

        function getData (breakdown, size) { // level, page
            var config = {
                selectedBreakdown: ds.selectedBreakdown,
                breakdown: breakdown,
                size: size,
            };
            var deferred = $q.defer();
            ds.endpoint.getData(config).then(function (breakdown) {
                notifyListeners(EVENTS.ON_LOAD, breakdown);
                applyBreakdown(breakdown);
                deferred.resolve(breakdown);
            }, function (error) {
                deferred.reject(error);
            });

            return deferred.promise;
        }

        // request base
        // breakdowns -> request more/initial

        function getData2 (level) {
            if (level > 0) {
                // traverse whole tree and retrieve level ids
            }
            var config = {
                level: level,
                breakdown: ds.selectedBreakdown.slice(0, level + 1),
                positions: [[1, 1], [1, 2]],
            };
        }

        function getElements (level) {

        }

        function onLoad (scope, callback) {
            registerListener(EVENTS.ON_LOAD, scope, callback);
        }

        function registerListener (event, scope, callback) {
            var handler = $rootScope.$on(event, callback);
            scope.$on('$destroy', handler);
        }

        function notifyListeners (event, data) {
            $rootScope.$emit(event, data);
        }
    }

    return {
        createInstance: function (endpoint) {
            return new DataSource(endpoint);
        },
    };
}]);
