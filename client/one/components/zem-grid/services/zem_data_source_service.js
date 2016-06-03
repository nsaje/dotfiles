/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceService', ['$rootScope', '$http', '$q', function ($rootScope, $http, $q) { // eslint-disable-line max-len

    //
    // DataSource is responsible for fetching data with help of passed Endpoint and
    // building internal representation of fetched data as a tree data structure.
    // Each level in tree represents requested breakdown level with data, while its child nodes
    // are breakdown data for the next level.
    //
    // L0 (initial level) -> totals + rows for L1 data === base level request
    // L(x) -> data for level x with optional breakdowns for level (x+1)
    //
    // L(x)
    //  --> stats (data - key:value dict)
    //  --> breakdown
    //      --> breakdown_id
    //      --> rows [L(x+1)]
    //      --> pagination {from, to, size, count}
    //


    // Definition of events used internally in DataSource
    // External listeners are registered through dedicated methods (e.g. onLoad)
    var EVENTS = {
        ON_LOAD: 'zem-data-source-on-load',
        ON_SAVE: 'zem-data-source-on-save',
        ON_STATS_UPDATED: 'zem-data-source-on-stats-updated',
        ON_DATA_UPDATED: 'zem-data-source-on-data-updated',
    };

    function DataSource (endpoint) {
        var ds = this;

        var data = null;

        var config = {
            order: '-clicks',
        };

        // selectedBreakdown defines currently configured breakdown
        // Default value is configured after retrieving metadata
        var selectedBreakdown = null;

        // Define default pagination (limits) for all levels when
        // size is not passed when requesting new data
        // TODO: default values will be defined by Breakdown selector (TBD)
        var defaultPagination = [20, 3, 5, 7];

        //
        // Public API
        //
        this.getData = getData;
        this.getMetaData = getMetaData;
        this.saveData = saveData;

        this.setDateRange = setDateRange;
        this.setOrder = setOrder;
        this.setBreakdown = setBreakdown;
        this.getDateRange = getDateRange;
        this.getOrder = getOrder;
        this.getBreakdown = getBreakdown;

        this.onLoad = onLoad;
        this.onStatsUpdated = onStatsUpdated;
        this.onDataUpdated = onDataUpdated;

        //
        // Definitions
        //
        function getMetaData () {
            var deferred = $q.defer();
            endpoint.getMetaData().then(function (metaData) {
                // Base level always defines only one breakdown and
                // is available as first element in breakdownGroups
                var baseLevelBreakdown = metaData.breakdownGroups[0];
                selectedBreakdown = [baseLevelBreakdown.breakdowns[0]];
                deferred.resolve(metaData);
            });
            return deferred.promise;
        }

        function getData (breakdown, size) {
            var level = 1;
            var offset, limit;
            var breakdowns = [];
            if (breakdown) {
                level = breakdown.level;
                offset = breakdown.pagination.limit;
                limit = size;
                breakdowns = [breakdown];
            } else {
                initializeRoot();
            }

            return getDataByLevel(level, breakdowns, offset, limit);
        }

        function getDataByLevel (level, breakdowns, offset, limit) {
            //
            // Fetches data for passed breakdowns (pagination - offset and limit) at the same time.
            // All retrieved data is applied to data tree and if not the last level subsequent data is fetch,
            // with newly retrieved breakdowns (breakdownIds)
            //
            var config = prepareConfig(level, breakdowns, offset, limit);

            breakdowns.forEach(function (breakdown) {
                breakdown.meta.loading = true;
            });

            var deferred = $q.defer();
            endpoint.getData(config).then(function (breakdowns) {
                applyBreakdowns(breakdowns);
                if (level < selectedBreakdown.length) {
                    // Chain request for each successive level
                    var childBreakdowns = getChildBreakdowns(breakdowns);
                    var promise = getDataByLevel(level + 1, childBreakdowns);
                    deferred.resolve(promise);
                } else {
                    deferred.resolve(data);
                }
            }).finally(function () {
                breakdowns.forEach(function (breakdown) {
                    breakdown.meta.loading = false;
                });
            });

            return deferred.promise;
        }

        function saveData (value, stats, column) {
            // TODO: Notifications (onSave)
            var oldValue = stats.data[column.field];
            var deferred = $q.defer();
            endpoint.saveData(value, stats, column).then(function () {
                stats.data[column.field] = value;
                notifyListeners(EVENTS.ON_STATS_UPDATED, stats, column);
                deferred.resolve();
            }, function (err) {
                stats.data[column.field] = oldValue;
                deferred.reject(err);
            });
            return deferred.promise;
        }

        function prepareConfig (level, breakdowns, offset, limit) {
            if (!offset) offset = 0;
            if (!limit) limit = defaultPagination[level - 1];
            var newConfig = {
                level: level,
                offset: offset,
                limit: limit,
                breakdown: selectedBreakdown.slice(0, level),
                breakdownPage: breakdowns.map(function (breakdown) {
                    return breakdown.breakdownId;
                }),
            };

            // Extend configs with DataSource configuration (dates, orders, etc.)
            angular.extend(newConfig, config);

            return newConfig;
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
            notifyListeners(EVENTS.ON_DATA_UPDATED, data);
        }

        function applyBreakdown (breakdown) {
            // Add breakdown to current data tree
            // Notify listeners, to give them chance to modify data,
            // initialize expected data structures
            notifyListeners(EVENTS.ON_LOAD, breakdown);
            initializeRowsData(breakdown);
            if (breakdown.level === 1 && breakdown.pagination.offset === 0) {
                data.breakdown = breakdown;
                data.breakdown.meta = {};
                data.stats = breakdown.totals;
                return;
            }

            // Find breakdown by id and apply partial breakdown data
            var current = findBreakdown(breakdown.breakdownId);
            current.rows = current.rows.concat(breakdown.rows);
            current.pagination.limit = current.rows.length;
            current.pagination.count = breakdown.pagination.count;
        }

        function findBreakdown (breakdownId, subtree) {
            // Traverse breakdown tree to find breakdown by breakdownId
            // If subtree (breakdown) is not passed start with base one
            if (!subtree) subtree = data.breakdown;
            if (subtree.breakdownId === breakdownId) {
                return subtree;
            }

            for (var i = 0; i < subtree.rows.length; ++i) {
                var row = subtree.rows[i];
                if (row.breakdown) {
                    var res = findBreakdown(breakdownId, row.breakdown);
                    if (res) return res;
                }
            }
            return null;
        }

        function initializeRoot () {
            data = { // Root node - L0
                breakdown: null,
                stats: null,
                level: 0,
                meta: {},
            };
            notifyListeners(EVENTS.ON_DATA_UPDATED, data);
        }

        function initializeRowsData (breakdown) {
            // Prepare empty breakdown for non-leaf (will be breakdown in future) nodes
            if (breakdown.level >= selectedBreakdown.length) return;

            breakdown.rows.forEach(function (row) {
                row.breakdown = {
                    level: breakdown.level + 1,
                    breakdownId: row.breakdownId,
                    pagination: {
                        offset: 0,
                        limit: 0,
                        count: -1,
                    },
                    rows: [],
                    meta: {},
                };
                delete row.breakdownId;
            });
        }

        function setDateRange (dateRange) {
            config.startDate = dateRange.startDate;
            config.endDate = dateRange.endDate;
        }

        function setOrder (order) {
            config.order = order;
        }

        function setBreakdown (breakdown) {
            selectedBreakdown = breakdown;
        }

        function getDateRange () {
            return {
                startDate: config.startDate,
                endDate: config.endDate,
            };
        }

        function getOrder () {
            return config.order;
        }

        function getBreakdown () {
            return selectedBreakdown;
        }

        function onLoad (scope, callback) {
            registerListener(EVENTS.ON_LOAD, scope, callback);
        }

        function onStatsUpdated (scope, callback) {
            registerListener(EVENTS.ON_STATS_UPDATED, scope, callback);
        }

        function onDataUpdated (scope, callback) {
            registerListener(EVENTS.ON_DATA_UPDATED, scope, callback);
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
