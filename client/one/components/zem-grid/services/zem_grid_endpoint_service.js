/* globals oneApp, angular */
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
            var deferred = createAbortableDefer();
            var data = zemGridEndpointApiConverter.convertConfigToApi(config);
            var httpConfig = {timeout: deferred.abortPromise};

            $http.post(url, {params: data}, httpConfig).success(function (data) {
                var breakdowns = data.data;
                breakdowns = breakdowns.map(function (breakdown) {
                    breakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(config, breakdown, metaData);
                    checkPaginationCount(config, breakdown);
                    return breakdown;
                });

                if (config.level === 1) { // Base level data comes with some additional metadata (e.g. goals)
                    extendMetaData(breakdowns[0], metaData);
                }

                deferred.resolve(breakdowns);
            }).error(function (data) {
                deferred.reject(data);
            });
            return deferred.promise;
        };

        this.saveData = function (value, row, column) {
            var api = zemGridEndpointApi.getApi(metaData.level, metaData.breakdown, column);

            var deferred = $q.defer();
            var levelEntityId = metaData.id;
            var breakdownEntityId = row.breakdownId;
            api.save(levelEntityId, breakdownEntityId, value).then(function (data) {
                var convertedField = zemGridEndpointApiConverter.convertField(data[column.field], column.type);
                data = angular.extend({}, row.stats[column.field], convertedField);
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
            // In case that pagination.count is not provided or is less then 0,
            // we can check if returned data size is less then
            // requested one -- in that case set the count to
            // the current size od data
            var pagination = breakdown.pagination;
            if (pagination.count == undefined || pagination.count === null || pagination.count < 0) {
                if (config.limit > pagination.limit) {
                    pagination.count = pagination.offset + pagination.limit;
                }
            }
            pagination.complete = (pagination.offset + pagination.limit) === pagination.count;
        }
    }

    function createAbortableDefer () {
        var deferred = $q.defer();
        var deferredAbort = $q.defer();
        deferred.promise.abort = function () {
            deferredAbort.resolve();
        };
        deferred.promise.finally(
            function () {
                deferred.promise.abort = angular.noop;
            }
        );

        deferred.abortPromise = deferredAbort.promise;
        return deferred;
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
            ext: {} // extensions placeholder
        };
    }

    function extendMetaData (breakdown, metaData) {
        zemGridEndpointColumns.updateConversionGoalColumns(metaData.columns, breakdown.conversionGoals);
        zemGridEndpointColumns.updateOptimizationGoalColumns(metaData.columns, breakdown.campaignGoals);

        if (breakdown.batches) {
            metaData.ext.batches = breakdown.batches;
            delete breakdown.batches;
        }

        metaData.ext.enablingAutopilotSourcesAllowed = true;
        if (breakdown.enablingAutopilotSourcesAllowed !== undefined) {
            metaData.ext.enablingAutopilotSourcesAllowed = breakdown.enablingAutopilotSourcesAllowed;
            delete breakdown.enablingAutopilotSourcesAllowed;
        }
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
