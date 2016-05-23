/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', 'zemGridService', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    //
    // DataSource is responsible for fetching data with help of passed Endpoint and
    // building internal representation of fetched data as a tree data structure.
    // Each level in tree represents requested breakdown level with data, while its child nodes
    // are breakdown data for the next level.
    //
    // L0 (initial levle) -> totals + rows for L1 data === base level request
    // L(x) -> data for level x with optinal breakdowns for level (x+1)
    //
    // L(x)
    //  --> stats (data - key:value dict)
    //  --> breakdown
    //      --> breakdown_id
    //      --> rows [L(x+1)]
    //      --> pagination {from, to, size, count}
    //


    var EVENTS = {
        ON_LOAD: 'zem-data-source-on-load',
    };

    function DataSource (endpoint) {
        var ds = this;

        this.data = null;
        this.endpoint = endpoint;
        this.availableBreakdowns = endpoint.availableBreakdowns;
        this.selectedBreakdown = endpoint.defaultBreakdown;
        this.defaultPagination = [20, 3, 5, 7];

        this.getData = getData;
        this.getMetaData = getMetaData;
        this.onLoad = onLoad;

        function getMetaData () {
            var config = {
                selectedBreakdown: ds.selectedBreakdown,
            };
            return ds.endpoint.getMetaData(config);
        }

        function getData (breakdown, size) {
            var level = 1;
            var offset, limit, breakdowns;
            if (breakdown) {
                level = breakdown.level;
                offset = breakdown.pagination.limit;
                limit = size;
                breakdowns = [breakdown];
            }
            return getDataByLevel(level, breakdowns, offset, limit);
        }

        function getDataByLevel (level, breakdowns, offset, limit) {
            if (!offset) offset = 0;
            if (!limit) limit = ds.defaultPagination[level - 1];
            if (!breakdowns) breakdowns = [];
            var config = {
                start_date: '2016-05-15',
                end_date: '2016-05-20',
                order: '-clicks',
                level: level,
                offset: offset,
                limit: limit,
                breakdown: ds.selectedBreakdown.slice(0, level),
                breakdown_page: breakdowns.map(function (breakdown) {
                    return breakdown.breakdownId;
                }),
            };

            var deferred = $q.defer();
            ds.endpoint.getData(config).then(function (breakdowns) {
                if (!breakdowns) {
                    deferred.resolve(ds.data);
                    return;
                }

                applyBreakdowns(breakdowns);
                deferred.notify(ds.data);
                if (level < ds.selectedBreakdown.length) {
                    // Chain request for each successive level
                    var childBreakdowns = getChildBreakdowns(breakdowns);
                    var promise = getDataByLevel(level + 1, childBreakdowns);
                    deferred.resolve(promise);
                } else {
                    deferred.resolve(ds.data);
                }
            });

            return deferred.promise;
        }

        function getChildBreakdowns (breakdowns) {
            var childBreakdowns = [];
            breakdowns.forEach(function (breakdown) {
                childBreakdowns = childBreakdowns.concat(breakdown.rows.map(function (row) {
                    return row.breakdown;
                }));
            });
            return childBreakdowns;
        }

        function applyBreakdowns (breakdowns) {
            breakdowns.forEach(function (breakdown) {
                applyBreakdown(breakdown);
            });
        }

        function applyBreakdown (breakdown) {
            notifyListeners(EVENTS.ON_LOAD, breakdown);
            initializeRowsData(breakdown);
            if (breakdown.level === 1 && breakdown.pagination.offset === 0) {
                initializeData(breakdown);
                return;
            }

            var current = findBreakdown(breakdown.breakdownId);
            current.rows = current.rows.concat(breakdown.rows);
            current.pagination.limit = current.rows.length;
            current.pagination.count = breakdown.pagination.count;
        }

        function findBreakdown (breakdownId, subtree) {
            // Traverse breakdown tree to find breakdown by breakdownId
            // If subtree (breakdown) is not passed start with base one
            if (!subtree) subtree = ds.data.breakdown;
            if (subtree.breakdownId === breakdownId) {
                return subtree;
            }
            var res = null;
            subtree.rows.forEach(function (row) {
                if (row.breakdown) {
                    var temp = findBreakdown(breakdownId, row.breakdown);
                    if (temp) res = temp;
                }
            });
            return res;
        }

        function initializeData (breakdown) {
            ds.data = {
                breakdown: breakdown,
                stats: breakdown.stats,
                level: 0,
            };
            delete breakdown.stats;
        }

        function initializeRowsData (breakdown) {
            // Prepare empty breakdown for non-leaf (will be breakdown in future) nodes
            if (breakdown.level < ds.selectedBreakdown.length) {
                breakdown.rows.forEach(function (row) {
                    // row = { stats, position }
                    row.breakdown = {
                        level: breakdown.level + 1,
                        breakdownId: row.breakdownId,
                        pagination: {
                            from: 0,
                            to: 0,
                            size: 0,
                        },
                        rows: [],
                    };
                    delete row.breakdownId;
                });
            }
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
