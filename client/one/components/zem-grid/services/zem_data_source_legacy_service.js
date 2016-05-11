/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceLegacyService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    var EVENTS = {
        ON_LOAD: 'zem-data-source-on-load',
    };

    function DataSource () {
        // Pagination - AllAccounts, ContentAds
        // Id - Account, Campaing, AdGroup (w/o AllAccounts)
        // API Url : [id], [page, size], startDate, endDate, order

        var ds = this;

        this.data = null;

        this.setEndpoint = setEndpoint;
        this.setColumns = setColumns;
        this.setDateRange = setDateRange;
        this.getData = getData;

        // Events
        this.onLoad = onLoad;

        function setColumns (columns) {
            ds.columns = columns;
        }

        function setEndpoint (endpoint) {
            ds.endpoint = endpoint;
        }

        function setDateRange (startDate, endDate) {
            ds.startDate = startDate;
            ds.endDate = endDate;
        }

        function getData (breakdown, size) {
            var deferred = $q.defer();

            var level = 0;
            var page = 1;

            if (!size) {
                size = 10;
            }

            if (breakdown) {
                level = 1;
                page = (breakdown.pagination.to) / size + 1;
            }
            ds.endpoint.get(page, size, ds.startDate, ds.endDate, '-cost').then(function (data) {

                notifyListeners(EVENTS.ON_LOAD, data);
                breakdown = parseLegacyData(data, level);
                applyBreakdown(breakdown);
                deferred.resolve(breakdown);

                // TODO: meta data - sync status, data status, postclick metrics
                // TODO: Notify ctrl (rows mapping - e.g. links)
                // TODO: Notify ctrl (location.search)

            }, function (error) {
                deferred.reject(error);
            });

            return deferred.promise;
        }

        function parseLegacyData (data, level) {
            var totals = {
                breakdown: {
                    position: [data.pagination.startIndex + 1],
                    pagination: {
                        count: data.pagination.count,
                        from: data.pagination.startIndex,
                        to: data.pagination.endIndex,
                        size: data.pagination.size,
                    },
                    rows: data.rows.map(function (row) {
                        return {
                            stats: row,
                        };
                    }),
                    level: 1,
                },
                stats: data.totals,
            };

            var breakdown = {
                rows: [totals],
                level: 0,
                meta: {
                    columns: ds.columns,
                },
            };

            if (level === 1)
                return breakdown.rows[0].breakdown;
            return breakdown;
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
        createInstance: function () {
            return new DataSource();
        },
    };
}]);
