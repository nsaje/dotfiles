/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    var EVENTS = {
        ON_LOAD : 'zem-data-source-on-load'
    };

    function DataSource (endpoint) {
        var ds = this;

        this.defaultPagination = [2, 3, 5, 7];
        this.data = null;
        this.endpoint = endpoint;
        this.breakdowns = endpoint.breakdowns;

        this.getData = getData;
        this.getMetaData = getMetaData;

        this.onLoad = onLoad;

        function prepareBreakdownConfig (breakdown, size) {
            var level = 0;
            if (breakdown) level = breakdown.level;

            var ranges = [];
            for (var i = 1; i <= ds.endpoint.breakdowns.length; ++i) {
                var from = 0;
                var to = ds.defaultPagination[i - 1];
                if (breakdown) {
                    if (i < breakdown.level) {
                        from = breakdown.position[i];
                        to = from + 1;
                    } else if (breakdown.level === i) {
                        from = breakdown.pagination.to;
                        if (size) {
                            if (size > 0) to = from + size;
                            else to = -1;
                        } else {
                            to = from + ds.defaultPagination[i - 1];
                        }
                    }
                }
                ranges.push([from, to].join('|'));
            }

            return {
                breakdown: breakdown,
                size: size,
                params: {
                    breakdowns: ds.endpoint.breakdowns.join(','),
                    ranges: ranges.join(','),
                    level: level,
                },
            };
        }

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
            var config = prepareBreakdownConfig();
            return ds.endpoint.getMetaData(config);
        }

        function getData (breakdown, size) { // level, page
            var config = prepareBreakdownConfig(breakdown, size);
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
