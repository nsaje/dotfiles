/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'api', function ($rootScope, $controller, $http, $q, $timeout, api) { // eslint-disable-line max-len

    function MockEndpoint () {
        var url = '/api/stats/testdata/';
        this.availableBreakdowns = ['ad_group', 'age', 'sex', 'date'];
        this.defaultBreakdown = ['ad_group', 'age', 'date'];
        this.defaultPagination = [2, 3, 5, 7];

        this.getMetaData = function (config) {
            var deferred = $q.defer();
            $http.get(url, this.createQueryParams(config)).success(function (data) {
                var breakdown = data.data[0];
                deferred.resolve(breakdown.meta);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        this.getData = function (config) {
            var deferred = $q.defer();
            $http.get(url, this.createQueryParams(config)).success(function (data) {
                deferred.resolve(data.data[0]);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        this.createQueryParams = function (config) {
            var breakdown = config.breakdown;
            var size = config.size;
            var level = 0;
            if (breakdown) level = breakdown.level;

            var ranges = [];
            for (var i = 1; i <= config.selectedBreakdown.length; ++i) {
                var from = 0;
                var to = this.defaultPagination[i - 1];
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
                            to = from + this.defaultPagination[i - 1];
                        }
                    }
                }
                ranges.push([from, to].join('|'));
            }

            return {
                params: {
                    breakdowns: config.selectedBreakdown.join(','),
                    ranges: ranges.join(','),
                    level: level,
                },
            };
        };
    }

    function LegacyEndpoint (tableApi, columns) {
        this.columns = columns;
        this.tableApi = tableApi;
        this.availableBreakdowns = ['campaign', 'source', 'device', 'week'];
        this.defaultBreakdown = [];
        this.defaultPagination = [2, 3, 5, 7];

        this.getMetaData = function () {
            var deferred = $q.defer();
            deferred.resolve({
                columns: columns,
            });
            return deferred.promise;
        };

        this.getData = function (config) {
            var deferred = $q.defer();

            var page = 1;
            var size = 10;

            if (config && config.size) {
                size = config.size;
            }

            if (config && config.breakdown) {
                // Find optimal page size to capture desired range (from-to)
                // Additional rows are sliced when parsing data
                var to = config.breakdown.pagination.to + size;
                while (true) {
                    page = Math.floor(config.breakdown.pagination.to / size) + 1;
                    if (page * size >= to) {
                        break;
                    }
                    size++;
                }
            }

            this.tableApi.get(page, size, null, null, '-cost').then(function (data) {
                var breakdown = this.parseLegacyData(config, data);
                deferred.resolve(breakdown);
            }.bind(this), function (error) {
                deferred.reject(error);
            });
            return deferred.promise;
        };

        this.parseLegacyData = function (config, data) {
            var breakdownL1 = {
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
            };

            if (config && config.breakdown) {
                // Slice additional rows if any
                var diff;
                var from = config.breakdown.pagination.to + 1;
                var to = config.size + from - 1;
                if (breakdownL1.pagination.from < from) {
                    diff = from - breakdownL1.pagination.from;
                    breakdownL1.pagination.from = from;
                    breakdownL1.pagination.size -= diff;
                    breakdownL1.rows = breakdownL1.rows.slice(diff);
                }
                if (breakdownL1.pagination.to > to) {
                    diff = breakdownL1.pagination.from - to;
                    breakdownL1.pagination.to = to;
                    breakdownL1.pagination.size -= diff;
                    breakdownL1.rows = breakdownL1.rows.slice(0, config.size);
                }

                return breakdownL1;
            }

            var breakdownL0 = {
                rows: [{
                    breakdown: breakdownL1,
                    stats: data.totals,
                }],
                level: 0,
                meta: {
                    columns: this.columns,
                },
            };
            return breakdownL0;
        };
    }

    function getLegacyColumns (ctrl) {
        // HACK (legacy support): access columns variable from corresponded controller
        var mainScope = angular.element(document.querySelectorAll('[ui-view]')).scope();
        var scope = mainScope.$new();
        try {
            $controller(ctrl, {$scope: scope});
        } catch (e) {
            // just ignore exception - only scope.columns is needed
        }
        return scope.columns;
    }

    return {
        createMockEndpoint: function () {
            return new MockEndpoint();
        },
        createAllAccountsEndpoint: function () {
            var columns = getLegacyColumns('AllAccountsAccountsCtrl');
            return new LegacyEndpoint(api.accountAccountsTable, columns);
        },
        createLegacyEndpoint: function (legacyApi, legacyCtrl) {
            var columns = getLegacyColumns(legacyCtrl);
            return new LegacyEndpoint(legacyApi, columns);
        },
    };
}]);
