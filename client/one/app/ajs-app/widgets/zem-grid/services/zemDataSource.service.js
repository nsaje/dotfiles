angular
    .module('one.widgets')
    .factory('zemDataSourceService', function($rootScope, $http, $q) {
        // eslint-disable-line max-len

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
            ON_STATS_UPDATED: 'zem-data-source-on-stats-updated',
            ON_DATA_UPDATED: 'zem-data-source-on-data-updated',
            ON_ROW_UPDATED: 'zem-data-source-on-row-updated',
        };

        var FILTER = {
            FILTERED_AGENCIES: 1,
            FILTERED_ACCOUNT_TYPES: 2,
            FILTERED_MEDIA_SOURCES: 3,
            SHOW_ARCHIVED_SOURCES: 4,
            SHOW_BLACKLISTED_PUBLISHERS: 5,
        };

        function DataSource(endpoint, $scope) {
            // Scope is used for notifying listeners
            // FIXME WORKAROUND: Using rootScope causes consistency problems between the views
            //   ! proper solution is need, but for now use passed $scope (provided by host controller)
            $scope = $scope || $rootScope;

            var metaData = null;
            var data = null;
            var activeLoadRequests = [];
            var saveRequestInProgress = false;

            var config = {
                order: '-clicks',
            };

            // selectedBreakdown defines currently configured breakdown
            // Default value is configured after retrieving metadata
            var selectedBreakdown = null;

            // Define default pagination (limits) for all levels when
            // size is not passed when requesting new data
            // TODO: default values will be defined by Breakdown selector (TBD)
            var defaultPagination = [60, 4, 5, 7];

            initializeRoot();

            //
            // Public API
            //
            this.FILTER = FILTER;
            this.getData = getData;
            this.getMetaData = getMetaData;
            this.loadData = loadData;
            this.loadMetaData = loadMetaData;
            this.saveData = saveData;
            this.updateData = updateData;
            this.editRow = editRow;

            this.isSaveRequestInProgress = isSaveRequestInProgress;

            this.setOrder = setOrder;
            this.setFilter = setFilter;
            this.setDateRange = setDateRange;
            this.setBreakdown = setBreakdown;
            this.getOrder = getOrder;
            this.getFilter = getFilter;
            this.getDateRange = getDateRange;
            this.getBreakdown = getBreakdown;
            this.getBreakdownLevel = getBreakdownLevel;

            this.onLoad = onLoad;
            this.onStatsUpdated = onStatsUpdated;
            this.onDataUpdated = onDataUpdated;
            this.onRowUpdated = onRowUpdated;

            //
            // Definitions
            //
            function getData() {
                return data;
            }

            function getMetaData() {
                return metaData;
            }

            function loadMetaData(forceFetch) {
                if (metaData && !forceFetch) return $q.resolve(metaData);

                var deferred = $q.defer();
                endpoint.getMetaData().then(function(_metaData) {
                    // Base level always defines only one breakdown and
                    // is available as first element in breakdownGroups
                    metaData = _metaData;
                    var baseLevelBreakdown =
                        metaData.breakdownGroups.base.breakdowns[0];
                    if (!selectedBreakdown) {
                        selectedBreakdown = [baseLevelBreakdown];
                    }
                    deferred.resolve(metaData);
                });
                return deferred.promise;
            }

            function loadData(breakdown, size) {
                var level = 1;
                var offset, limit;
                var breakdowns = [];
                if (breakdown) {
                    level = breakdown.level;
                    offset = breakdown.pagination.limit;
                    limit = size;
                    breakdowns = [breakdown];
                } else {
                    abortActiveLoadRequests();
                    initializeRoot();
                }

                // First make sure that meta-data is initialized and then fetch the requested data
                return loadMetaData().then(function() {
                    return getDataByLevel(level, breakdowns, offset, limit);
                });
            }

            function getDataByLevel(level, breakdowns, offset, limit) {
                //
                // Fetches data for passed breakdowns (pagination - offset and limit) at the same time.
                // All retrieved data is applied to data tree and if not the last level subsequent data is fetch,
                // with newly retrieved breakdowns (breakdownIds)
                //
                var deferred = $q.defer();
                var config = prepareConfig(level, breakdowns, offset, limit);
                var promise = endpoint.getData(config);

                var request = {promise: promise, config: config};
                activeLoadRequests.push(request);

                breakdowns.forEach(function(breakdown) {
                    breakdown.meta.loading = true;
                });

                promise
                    .then(
                        function(breakdowns) {
                            applyBreakdowns(breakdowns);
                            var childBreakdowns = getChildBreakdowns(
                                breakdowns
                            );
                            if (childBreakdowns.length > 0) {
                                // Chain request for each successive level
                                var promise = getDataByLevel(
                                    level + 1,
                                    childBreakdowns
                                );
                                deferred.resolve(promise);
                            } else {
                                deferred.resolve(data);
                            }
                        },
                        function(err) {
                            breakdowns.forEach(function(breakdown) {
                                breakdown.meta.error = true;
                            });
                            deferred.reject(err);
                        }
                    )
                    .finally(function() {
                        var idx = activeLoadRequests.indexOf(request);
                        if (idx > -1) activeLoadRequests.splice(idx, 1);
                        breakdowns.forEach(function(breakdown) {
                            breakdown.meta.loading = false;
                        });
                    });

                return deferred.promise;
            }

            function saveData(value, row, column) {
                if (saveRequestInProgress) {
                    return $q.reject();
                }

                var deferred = $q.defer();
                saveRequestInProgress = true;
                config.level = row.row ? row.row.level : 1;
                config.breakdown = getBreakdown();
                endpoint.saveData(value, row, column, config).then(
                    function(breakdown) {
                        updateData(breakdown);
                        saveRequestInProgress = false;
                        deferred.resolve(breakdown);
                    },
                    function(error) {
                        saveRequestInProgress = false;
                        deferred.reject(error);
                    }
                );
                return deferred.promise;
            }

            function editRow(row) {
                return endpoint.editRow(row);
            }

            function updateData(breakdown) {
                // For each row in breakdown patch find cached row by id and apply values
                var updatedStats = [];
                breakdown.rows.forEach(function(updatedRow) {
                    var row = findRow(updatedRow.breakdownId);
                    if (row) {
                        if (updatedRow.archived !== undefined) {
                            row.archived = updatedRow.archived;
                        }
                        if (updatedRow.stats) {
                            updateStats(row.stats, updatedRow.stats);
                            updatedStats.push(row.stats);
                            notifyListeners(EVENTS.ON_ROW_UPDATED, row);
                        }
                    }
                });

                if (breakdown.totals) {
                    updateStats(data.stats, breakdown.totals);
                    updatedStats.push(data.stats);
                }

                notifyListeners(EVENTS.ON_STATS_UPDATED, updatedStats);
            }

            function updateStats(stats, updatedStats) {
                Object.keys(updatedStats).forEach(function(field) {
                    var updatedField = updatedStats[field];
                    if (
                        updatedField !== undefined &&
                        updatedField.value !== undefined &&
                        stats[field] !== undefined
                    ) {
                        angular.extend(stats[field], updatedField);
                    }
                });
            }

            function prepareConfig(level, breakdowns, offset, limit) {
                if (!offset) offset = 0;
                if (!limit) limit = defaultPagination[level - 1];
                var newConfig = {
                    level: level,
                    offset: offset,
                    limit: limit,
                    breakdown: selectedBreakdown.slice(0, level),
                    breakdownParents: breakdowns.map(function(breakdown) {
                        return breakdown.breakdownId;
                    }),
                };

                // Extend configs with DataSource configuration (dates, orders, etc.)
                angular.extend(newConfig, config);

                return newConfig;
            }

            function abortActiveLoadRequests() {
                activeLoadRequests.forEach(function(request) {
                    request.promise.abort();
                });
                activeLoadRequests = [];
            }

            function isSaveRequestInProgress() {
                return saveRequestInProgress;
            }

            function getChildBreakdowns(breakdowns) {
                var childBreakdowns = [];
                breakdowns.forEach(function(breakdown) {
                    breakdown.rows.forEach(function(row) {
                        if (row.breakdown) {
                            if (row.group) {
                                var groupBreakdowns = getChildBreakdowns([
                                    row.breakdown,
                                ]);
                                childBreakdowns = childBreakdowns.concat(
                                    groupBreakdowns
                                );
                            } else {
                                childBreakdowns.push(row.breakdown);
                            }
                        }
                    });
                });
                return childBreakdowns;
            }

            function applyBreakdowns(breakdowns) {
                breakdowns.forEach(function(breakdown) {
                    applyBreakdown(breakdown);
                });
                notifyListeners(EVENTS.ON_DATA_UPDATED, data);
            }

            function applyBreakdown(breakdown) {
                // Add breakdown to current data tree
                // Notify listeners, to give them chance to modify data,
                // initialize expected data structures
                notifyListeners(EVENTS.ON_LOAD, breakdown);
                if (breakdown.level < selectedBreakdown.length) {
                    breakdown.rows.forEach(function(node) {
                        initializeNodeBreakdown(node, breakdown.level + 1);
                    });
                }
                if (
                    breakdown.level === 1 &&
                    breakdown.pagination.offset === 0
                ) {
                    data.breakdown = breakdown;
                    data.breakdown.meta = {};
                    data.stats = breakdown.totals;
                    delete breakdown.totals;
                    return;
                }

                // Find breakdown by id and apply partial breakdown data
                var current = findBreakdown(breakdown.breakdownId);
                mergeRows(current.rows, breakdown.rows);
                current.pagination.limit = current.rows.length;
                current.pagination.count = breakdown.pagination.count;
                current.pagination.complete = breakdown.pagination.complete;
            }

            function mergeRows(rows, newRows) {
                // Find row by breakdownId and merge it (happens with group updates)
                // or if not found push it to collection (usual flow)
                newRows.forEach(function(newRow) {
                    var row = rows.filter(function(r) {
                        return r.breakdownId === newRow.breakdownId;
                    })[0];
                    if (row && row.breakdown) {
                        applyBreakdown(newRow.breakdown);
                    } else {
                        rows.push(newRow);
                    }
                });
            }

            function findBreakdown(breakdownId, subtree) {
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

            function findRow(breakdownId, subtree) {
                // Traverse breakdown tree to find row by breakdownId
                // If subtree (breakdown) is not passed start with base one
                if (!subtree) subtree = data.breakdown;

                for (var i = 0; i < subtree.rows.length; ++i) {
                    var row = subtree.rows[i];
                    if (row.breakdownId === breakdownId) {
                        return row;
                    }
                    if (row.breakdown) {
                        var res = findRow(breakdownId, row.breakdown);
                        if (res) return res;
                    }
                }
                return null;
            }

            function initializeRoot() {
                data = {
                    // Root node - L0
                    breakdown: null,
                    stats: null,
                    level: 0,
                    meta: {},
                };
                notifyListeners(EVENTS.ON_DATA_UPDATED, data);
            }

            function initializeNodeBreakdown(node, level) {
                if (node.group) {
                    // Special case for groups - initialize breakdown on childs
                    node.breakdown.rows.forEach(function(row) {
                        initializeNodeBreakdown(row, level);
                    });
                    return;
                }
                // Prepare empty breakdown for non-leaf (will be breakdown in future) nodes
                node.breakdown = {
                    level: level,
                    breakdownId: node.breakdownId,
                    pagination: {
                        offset: 0,
                        limit: 0,
                        count: -1,
                    },
                    rows: [],
                    meta: {},
                };
            }

            function setOrder(order, fetch) {
                config.order = order;
                if (fetch) {
                    return loadData();
                }
            }

            function setDateRange(dateRange) {
                config.startDate = dateRange.startDate;
                config.endDate = dateRange.endDate;
            }

            function setFilter(filter, value, fetch) {
                switch (filter) {
                    case FILTER.FILTERED_AGENCIES:
                        config.filteredAgencies = value;
                        break;
                    case FILTER.FILTERED_ACCOUNT_TYPES:
                        config.filteredAccountTypes = value;
                        break;
                    case FILTER.FILTERED_MEDIA_SOURCES:
                        config.filteredSources = value;
                        break;
                    case FILTER.SHOW_ARCHIVED_SOURCES:
                        config.showArchived = value;
                        break;
                    case FILTER.SHOW_BLACKLISTED_PUBLISHERS:
                        config.showBlacklistedPublishers = value;
                        break;
                }

                if (fetch) {
                    return loadData();
                }
            }

            function setBreakdown(breakdown, fetch) {
                // Configures new breakdown for this DataSource and fetch missing data
                // Compare previous configured breakdown with new one and find out
                // which level levels can stay the same (re-fetching is not needed)
                var diff = findDifference(breakdown, selectedBreakdown);
                if (diff < 0) return fetch ? $q.resolve(data) : undefined;

                // Breakdown levels are 1-based therefor (diff + 1) is level
                // that is different and needs to be replaced, taking into account
                // current tree level (depth)
                var equalLevel = Math.min(getTreeLevel(), diff);
                var baseNodes = getNodesByLevel(equalLevel);
                var fetchSuccessiveLevels = breakdown.length > equalLevel;
                selectedBreakdown = breakdown;

                // Check if there is already an active request to retrieve data (breakdown)
                // that could be reused with new configuration. In case it is chain that request's
                // promise to avoid unnecessary re-fetch (abort + request)
                if (activeLoadRequests.length === 1) {
                    var request = activeLoadRequests[0];
                    var nextBreakdownRequest = selectedBreakdown.slice(
                        0,
                        equalLevel + 1
                    );
                    if (
                        angular.equals(
                            nextBreakdownRequest,
                            request.config.breakdown
                        )
                    ) {
                        return fetch ? request.promise : undefined;
                    }
                }

                // Abort all active requests that would lead to inconsistencies in data tree.
                abortActiveLoadRequests();

                // For all levels below remove all nodes and initialize new breakdown object (if needed)
                var childBreakdowns = [];
                baseNodes.forEach(function(node) {
                    if (fetchSuccessiveLevels) {
                        initializeNodeBreakdown(node, equalLevel + 1);
                        childBreakdowns.push(node.breakdown);
                    } else {
                        delete node.breakdown;
                    }
                });

                notifyListeners(EVENTS.ON_DATA_UPDATED, data);

                if (fetch) {
                    if (fetchSuccessiveLevels) {
                        return getDataByLevel(equalLevel + 1, childBreakdowns);
                    }

                    return $q.resolve(data);
                }
            }

            function getTreeLevel() {
                var level = 0;
                var node = data;
                while (node.breakdown && node.breakdown.rows.length > 0) {
                    node = node.breakdown.rows[0];
                    level += 1;
                }
                return level;
            }

            function getNodesByLevel(level, node, result) {
                if (!node) node = data;
                if (!result) result = [];
                if (!node.breakdown) return result;

                node.breakdown.rows.forEach(function(child) {
                    if (child.group || node.breakdown.level !== level) {
                        getNodesByLevel(level, child, result);
                    } else {
                        result.push(child);
                    }
                });

                return result;
            }

            function getOrder() {
                return config.order;
            }

            function getDateRange() {
                return {
                    startDate: config.startDate,
                    endDate: config.endDate,
                };
            }

            function getFilter(filter) {
                switch (filter) {
                    case FILTER.FILTERED_AGENCIES:
                        return config.filteredAgencies;
                    case FILTER.FILTERED_ACCOUNT_TYPES:
                        return config.filteredAccountTypes;
                    case FILTER.FILTERED_MEDIA_SOURCES:
                        return config.filteredSources;
                    case FILTER.SHOW_ARCHIVED_SOURCES:
                        return config.showArchived;
                    case FILTER.SHOW_BLACKLISTED_PUBLISHERS:
                        return config.showBlacklistedPublishers;
                }
            }

            function getBreakdown() {
                return selectedBreakdown;
            }

            function getBreakdownLevel() {
                return selectedBreakdown.length;
            }

            function findDifference(arr1, arr2) {
                var diff = -1;
                for (var i = 0; i < arr1.length; i++) {
                    if (arr1[i] === arr2[i]) {
                        continue;
                    } else {
                        diff = i;
                        break;
                    }
                }

                if (diff < 0 && arr2.length > arr1.length) {
                    return arr1.length;
                }

                return diff;
            }

            function onLoad(scope, callback) {
                return registerListener(EVENTS.ON_LOAD, scope, callback);
            }

            function onStatsUpdated(scope, callback) {
                return registerListener(
                    EVENTS.ON_STATS_UPDATED,
                    scope,
                    callback
                );
            }

            function onDataUpdated(scope, callback) {
                return registerListener(
                    EVENTS.ON_DATA_UPDATED,
                    scope,
                    callback
                );
            }

            function onRowUpdated(scope, callback) {
                return registerListener(EVENTS.ON_ROW_UPDATED, scope, callback);
            }

            function registerListener(event, scope, callback) {
                var handler = $scope.$on(event, callback);
                scope.$on('$destroy', handler);
                return handler;
            }

            function notifyListeners(event, data) {
                $scope.$emit(event, data);
            }
        }

        return {
            createInstance: function(endpoint, $scope) {
                return new DataSource(endpoint, $scope);
            },
        };
    });
