/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'api', function ($rootScope, $controller, $http, $q, $timeout, api) { // eslint-disable-line max-len

    function StatsEndpoint (baseUrl, ctrl) {
        this.availableBreakdowns = ['account', 'source', 'dma', 'day'];
        this.defaultBreakdown = ['account'];
        this.columns = getControllerColumns(ctrl);
        this.baseUrl = baseUrl;

        this.getMetaData = function () {
            var deferred = $q.defer();
            deferred.resolve({
                columns: this.columns,
            });
            return deferred.promise;
        };

        this.getData = function (config) {
            var url = baseUrl + config.breakdown.join('/') + '/';
            var deferred = $q.defer();
            var params = { // TODO: support all parameters
                start_date: '2016-01-01',
                end_date: '2016-05-01',
                offset: config.offset,
                limit: config.limit,
                order: '-clicks',
                breakdown: config.breakdown,
                breakdown_page: config.breakdownIds,
            }

            if (config.level == 1) {
                // Base level hack - partial data, pagination not working, etc.
                params.offset = 0;
                params.limit = 2;
                params.order = 'total_fee';
            }

            $http.post(url, { params: params}).
            success(function (data) {
                var breakdowns = data.data;
                breakdowns.forEach(function(breakdown){
                    breakdown.level = config.level;
                    breakdown.pagination.from = breakdown.pagination.offset;
                    breakdown.pagination.to = breakdown.pagination.offset + breakdown.pagination.limit;

                    if (config.level == 1) {
                        // Base level hack - partial data, pagination not working, etc.
                        breakdown.pagination.from = 0;
                        breakdown.pagination.to = breakdown.rows.length;
                        breakdown.stats = breakdown.totals;
                        breakdown.rows = breakdown.rows.map(function (row) {
                            return {
                                stats: row,
                                breakdownId: row.id,
                            }
                        });
                    }
                });
                deferred.resolve(data.data);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };
    }

    function getControllerColumns (ctrl) {
        //
        // HACK (legacy support): access columns variable from corresponded controller scope
        //
        var mainScope = angular.element(document.querySelectorAll('[ui-view]')).scope();
        var scope = mainScope.$new();
        try { $controller(ctrl, {$scope: scope}); } catch (e) { } // eslint-disable-line
        return scope.columns;
    }

    return {
        createAllAccountsEndpoint: function () {
            return new StatsEndpoint('/api/all_accounts/breakdown/', 'AllAccountsAccountsCtrl');
        },
    };
}]);
