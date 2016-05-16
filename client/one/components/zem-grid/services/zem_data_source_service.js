/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    var EVENTS = {
        ON_LOAD: 'zem-data-source-on-load',
    };

    function DataSource (endpoint) {
        var ds = this;

        this.data = null;
        this.endpoint = endpoint;
        this.breakdowns = endpoint.breakdowns;

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
            return ds.endpoint.getMetaData();
        }

        function getData (breakdown, size) { // level, page
            var config = {
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
