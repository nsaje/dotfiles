/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'api', function ($rootScope, $controller, $http, $q, $timeout, api) { // eslint-disable-line max-len

    function StatsEndpoint (baseUrl, ctrl) {
        this.availableBreakdowns = ['account', 'source', 'day'];
        this.defaultBreakdown = ['account', 'day'];
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
            $http.post(url, {params: config}).success(function (data) {
                var breakdowns = data.data;
                if (breakdowns) {
                    breakdowns.forEach(function (breakdown) {
                        convertFromApi(config, breakdown);
                        // check count ...
                    });
                }
                deferred.resolve(data.data);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };
    }

    function convertFromApi (config, breakdown) {
        breakdown.level = config.level;
        breakdown.breakdownId = breakdown.breakdown_id;
        breakdown.rows = breakdown.rows.map(function (row) {
            if (config.level > 1)
                row.breakdownName = row.breakdown_name;
            else
                row.breakdownName = row.account_name;

            return {
                stats: row,
                breakdownId: row.breakdown_id,
            };
        });
    }

    function getControllerColumns (ctrl) {
        //
        // HACK (legacy support): access columns variable from corresponded controller scope
        //
        var mainScope = angular.element(document.querySelectorAll('[ui-view]')).scope();
        var scope = mainScope.$new();
        try {
            $controller(ctrl, {$scope: scope});
        } catch (e) {
        } // eslint-disable-line

        // Replace first column type to text and field breakdown name, to solve
        // temporary problems with primary column content in level>1 breakdowns
        // FIXME: find appropriate solution for this problem (special type)
        scope.columns[0].field = 'breakdownName';
        scope.columns[0].type = 'text';
        return scope.columns;
    }

    return {
        createAllAccountsEndpoint: function () {
            return new StatsEndpoint('/api/all_accounts/breakdown/', 'AllAccountsAccountsCtrl');
        },
    };
}]);
