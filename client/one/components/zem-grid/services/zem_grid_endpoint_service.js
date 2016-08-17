/* globals oneApp, angular, constants */
/* eslint-disable camelcase*/

'use strict';

oneApp.factory('zemGridEndpointService', ['$http', '$q', 'zemGridEndpointApi', 'zemGridEndpointBreakdowns', 'zemGridEndpointColumns', 'zemNavigationService', function ($http, $q, zemGridEndpointApi, zemGridEndpointBreakdowns, zemGridEndpointColumns, zemNavigationService) { // eslint-disable-line max-len

    function EndpointService (metaData) {

        var api = zemGridEndpointApi.createInstance(metaData);

        this.getMetaData = function () {
            // Meta data is not yet fetched from backend,
            // therefor just return already fulfilled promise
            var deferred = $q.defer();
            deferred.resolve(metaData);
            return deferred.promise;
        };

        this.getData = function (config) {
            var deferred = $q.defer();
            var promise = api.get(config);
            promise.then(function (breakdowns) {
                breakdowns.forEach(function (breakdown) {
                    checkPaginationCount(config, breakdown);
                });

                // Base level data comes with some additional metadata (e.g. goals)
                if (config.level === 1) {
                    extendMetaData(breakdowns[0], metaData);
                }

                deferred.resolve(breakdowns);
            }, function (error) {
                deferred.reject(error);
            });

            deferred.promise.abort = promise.abort;
            return deferred.promise;
        };

        this.saveData = function (value, row, column, config) {
            var deferred = $q.defer();
            var data = {
                settings: {},
                config: config,
            };
            data.settings[column.field] = value;
            api.save(row.breakdownId, data).then(function (breakdown) {
                extendMetaData(breakdown, metaData);
                deferred.resolve(breakdown);
            }, function (err) {
                deferred.reject(err);
            });

            if (metaData.breakdown === constants.breakdown.AD_GROUP) {
                return chainNavigationServiceUpdate(row.breakdownId, deferred.promise);
            }
            return deferred.promise;
        };

        function chainNavigationServiceUpdate (adGroupId, promise) {
            // In case we are changing AdGroup settings, notify Navigation service to reload this AdGroup
            var deferred = $q.defer();
            zemNavigationService.notifyAdGroupReloading(adGroupId, true);
            promise.then(function (data) {
                zemNavigationService.reloadAdGroup(adGroupId);
                deferred.resolve(data);
            }, function (data) {
                zemNavigationService.notifyAdGroupReloading(adGroupId, false);
                deferred.reject(data);
            });
            return deferred.promise;
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

    function createMetaData (scope, level, id, breakdown) {
        // Replace first column type to text and field breakdown name, to solve
        // temporary problems with primary column content in level>1 breakdowns
        // FIXME: find appropriate solution for this problem (special type)
        var breakdownGroups = zemGridEndpointBreakdowns.createBreakdownGroups(scope, level, breakdown);
        var columns = zemGridEndpointColumns.createColumns(scope, level, getAvailableBreakdowns(breakdownGroups));
        var categories = zemGridEndpointColumns.createCategories(columns);

        return {
            id: id,
            level: level,
            breakdown: breakdown,
            columns: columns,
            categories: categories,
            breakdownGroups: breakdownGroups,
            ext: {} // extensions placeholder
        };
    }

    function getAvailableBreakdowns (breakdownGroups) {
        // Returns all structural breakdowns (text/query) available in group configuration
        return [].concat(
            breakdownGroups.base.breakdowns,
            breakdownGroups.structure.breakdowns
        ).map(function (breakdown) {
            return breakdown.query;
        });
    }

    function extendMetaData (breakdown, metaData) {
        zemGridEndpointColumns.updateConversionGoalColumns(metaData.columns, breakdown.conversionGoals);
        zemGridEndpointColumns.updateOptimizationGoalColumns(metaData.columns, breakdown.campaignGoals);

        if (breakdown.batches) {
            metaData.ext.batches = breakdown.batches;
            delete breakdown.batches;
        }

        if (breakdown.obBlacklistedCount) {
            metaData.ext.obBlacklistedCount = breakdown.obBlacklistedCount;
            delete breakdown.obBlacklistedCount;
        }

        metaData.ext.enablingAutopilotSourcesAllowed = true;
        if (breakdown.enablingAutopilotSourcesAllowed !== undefined) {
            metaData.ext.enablingAutopilotSourcesAllowed = breakdown.enablingAutopilotSourcesAllowed;
            delete breakdown.enablingAutopilotSourcesAllowed;
        }

        if (breakdown.adGroupAutopilotState !== undefined) {
            metaData.adGroupAutopilotState = breakdown.adGroupAutopilotState;
            delete breakdown.adGroupAutopilotState;
        }
    }

    function createEndpoint (metaData) {
        return new EndpointService(metaData);
    }


    return {
        createEndpoint: createEndpoint,
        createMetaData: createMetaData,
    };
}]);
