/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'api', function ($rootScope, $controller, $http, $q, $timeout, api) { // eslint-disable-line max-len
    //
    // Temporary endpoint to showcase how zem-grid is working with old (legacy) TableAPI
    // TODO: Remove LegacyEndpoint and create Endpoint for new Breakdowns API
    //
    function LegacyEndpoint (tableApi, columns) {
        this.columns = columns;
        this.tableApi = tableApi;
        this.availableBreakdowns = [];
        this.defaultBreakdown = [];

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
                while (true) { // eslint-disable-line
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

            // Slice additional rows if any
            if (config && config.breakdown) {
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
        //
        // HACK (legacy support): access columns variable from corresponded controller scope
        //
        var mainScope = angular.element(document.querySelectorAll('[ui-view]')).scope();
        var scope = mainScope.$new();
        try { $controller(ctrl, {$scope: scope}); } catch (e) { } // eslint-disable-line
        return scope.columns;
    }

    function createLegacyEndpoint (legacyApi, legacyCtrl) {
        var columns = getLegacyColumns(legacyCtrl);
        return new LegacyEndpoint(legacyApi, columns);
    }

    return {
        createLegacyEndpoint: createLegacyEndpoint,
        createAllAccountsEndpoint: function () {
            return createLegacyEndpoint(api.accountAccountsTable, 'AllAccountsAccountsCtrl');
        },
    };
}]);
