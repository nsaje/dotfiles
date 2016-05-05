/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) {

    var EVENTS = {
        PRE_GET_DATA: 'pre-get-data',
        POST_GET_DATA: 'post-get-data',
        PRE_GET_META_DATA: 'pre-get-meta-data',
        POST_GET_META_DATA: 'post-get-meta-data',
        PRE_UPDATE: 'pre-update',
        POST_UPDATE: 'post-update',
    };

    function DataSource () {
        var ds = this;

        this.EVENTS = EVENTS;
        this.breakdowns = ['ad_group', 'age', 'date'];
        this.endpoint = '/api/stats/testdata/';
        this.defaultPagination = [2, 3, 5];
        this.data = null;

        this.getData = getData;
        this.getMetaData = getMetaData;
        this.updateData = updateData;
        this.registerListener = registerListener;


        function prepareBreakdownConfig (breakdown, size) {
            var level = 0;
            if (breakdown) level = breakdown.level;

            var ranges = [];
            for (var i = 1; i <= ds.breakdowns.length; ++i) {
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
                params: {
                    breakdowns: ds.breakdowns.join(','),
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

        function getMetaData () { /* TODO */
        }

        function getData (breakdown, size) { // level, page
            var config = prepareBreakdownConfig(breakdown, size);
            var deferred = $q.defer();
            $http.get(ds.endpoint, config).success(function (data) {
                var breakdown = data.data[0];
                applyBreakdown(breakdown);
                deferred.resolve(breakdown);
                notifyListeners(DataSource.EVENTS.POST_GET_DATA, breakdown);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        }

        function updateData () { /* TODO */
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
