/* globals oneApp */
/* eslint-disable camelcase*/

'use strict';

oneApp.factory('zemGridEndpointService', ['$http', '$q', 'zemGridEndpointApi', 'zemGridEndpointBreakdowns', 'zemGridEndpointColumns', 'zemGridEndpointApiConverter', function ($http, $q, zemGridEndpointApi, zemGridEndpointBreakdowns, zemGridEndpointColumns, zemGridEndpointApiConverter) { // eslint-disable-line max-len

    function StatsEndpoint (baseUrl, metaData) {

        this.getMetaData = function () {
            // Meta data is not yet fetched from backend,
            // therefor just return already fulfilled promise
            var deferred = $q.defer();
            deferred.resolve(metaData);
            return deferred.promise;
        };

        this.getData = function (config) {
            var url = createUrl(baseUrl, config);
            var params = zemGridEndpointApiConverter.convertConfigToApi(config);
            var deferred = $q.defer();
            $http.post(url, {params: params}).success(function (data) {
                var breakdowns = data.data;
                breakdowns = breakdowns.map(function (breakdown) {
                    breakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(config, breakdown, metaData);
                    checkPaginationCount(config, breakdown);
                    return breakdown;
                });
                deferred.resolve(breakdowns);
            }).error(function (data) {
                deferred.reject(data);
            });
            return deferred.promise;
        };

        this.saveData = function (value, stats, column) {
            var api = zemGridEndpointApi.getApi(metaData.level, metaData.breakdown, column);

            var deferred = $q.defer();
            var levelEntityId = metaData.id;
            var breakdownEntityId = stats.breakdownId;
            api.save(levelEntityId, breakdownEntityId, value).then(function (data) {
                // TODO: handle data
                deferred.resolve(data);
            }, function (err) {
                deferred.reject(err);
            });
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
            pagination.complete = (pagination.offset + pagination.limit) === pagination.count;
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

        return {
            id: id,
            level: level,
            breakdown: breakdown,
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
