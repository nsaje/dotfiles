/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridEndpointService', ['$rootScope', '$controller', '$http', '$q', 'zemGridEndpointBreakdowns', 'zemGridEndpointColumns', 'zemGridEndpointApiConverter', function ($rootScope, $controller, $http, $q, zemGridEndpointBreakdowns, zemGridEndpointColumns, zemGridEndpointApiConverter) { // eslint-disable-line max-len

    function StatsEndpoint (baseUrl, metaData) {
        this.metaData = metaData;
        this.baseUrl = baseUrl;

        this.getMetaData = function () {
            // Meta data is not yet fetched from backend,
            // therefor just return already fulfilled promise
            var deferred = $q.defer();
            deferred.resolve(this.metaData);
            return deferred.promise;
        };

        var self = this; // TODO: Remove when column definitions are moved to a service
        this.getData = function (config) {
            var url = createUrl(baseUrl, config);
            config = zemGridEndpointApiConverter.convertToApi(config);
            var deferred = $q.defer();
            $http.post(url, {params: config}).success(function (data) {
                var breakdowns = data.data;
                breakdowns.forEach(function (breakdown) {
                    zemGridEndpointApiConverter.convertFromApi(config, breakdown, self.metaData);
                    checkPaginationCount(config, breakdown);
                });
                deferred.resolve(breakdowns);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        this.saveData = function (value, stats, column) {
            // TODO: actually save value - depends on Columns definitions refactorings...
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        };

        function createUrl (baseUrl, config) {
            var queries = config.breakdown.map(function (breakdown) {
                return breakdown.query;
            });
            return baseUrl + queries.join('/') + '/';
        }

        function checkPaginationCount (config, breakdown) {
            // In case that pagination.count is not provided,
            // we can check if returned data size is less then
            // requested one -- in that case set the count to
            // the current size od data
            var pagination = breakdown.pagination;
            if (pagination.count < 0) {
                if (config.limit > pagination.limit) {
                    pagination.count = pagination.offset + pagination.limit;
                }
            }
        }
    }

    function getUrl (level, id) {
        if (level === 'all_accounts') {
            return '/api/all_accounts/breakdown/';
        }
        return '/api/' + level + '/' + id + '/breakdown/';
    }

    function createMetaData (scope, level, id, breakdown) {
        // Replace first column type to text and field breakdown name, to solve
        // temporary problems with primary column content in level>1 breakdowns
        // FIXME: find appropriate solution for this problem (special type)
        var columns = zemGridEndpointColumns.createColumns(scope, level, breakdown);
        var categories = zemGridEndpointColumns.createCategories(columns);
        var breakdownGroups = zemGridEndpointBreakdowns.createBreakdownGroups(level, breakdown);

        columns[0].field = 'breakdownName';
        columns[0].type = 'text';

        return {
            id: id,
            level: level,
            columns: columns,
            categories: categories,
            breakdownGroups: breakdownGroups,
            localStoragePrefix: 'zem-grid-endpoint-' + level + '-' + breakdown,
        };
    }

    function createEndpoint (metaData) {
        var url = getUrl(metaData.level, metaData.id);
        return new StatsEndpoint(url, metaData);
    }


    return {
        createEndpoint: createEndpoint,
        createMetaData: createMetaData,
    };
}]);
