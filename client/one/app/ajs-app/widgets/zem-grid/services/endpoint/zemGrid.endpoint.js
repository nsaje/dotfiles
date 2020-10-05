/* eslint-disable camelcase*/

angular
    .module('one.widgets')
    .factory('zemGridEndpointService', function(
        $http,
        $q,
        zemGridEndpointApi,
        zemGridEndpointBreakdowns,
        zemGridEndpointColumns,
        zemNavigationService
    ) {
        // eslint-disable-line max-len

        function EndpointService(metaData) {
            var api = zemGridEndpointApi.createInstance(metaData);

            this.getMetaData = function() {
                // Meta data is not yet fetched from backend,
                // therefor just return already fulfilled promise
                var deferred = $q.defer();
                deferred.resolve(metaData);
                return deferred.promise;
            };

            this.getData = function(config) {
                var deferred = $q.defer();
                var promise = api.get(config);
                promise.then(
                    function(breakdowns) {
                        // Base level data comes with some additional metadata (e.g. goals)
                        if (config.level === 1) {
                            extendMetaData(breakdowns[0], metaData);
                        }

                        breakdowns.forEach(function(breakdown) {
                            extendPagination(breakdown);
                        });

                        deferred.resolve(breakdowns);
                    },
                    function(error) {
                        deferred.reject(error);
                    }
                );

                deferred.promise.abort = promise.abort;
                return deferred.promise;
            };

            this.saveData = function(value, row, column, config) {
                var deferred = $q.defer();
                var data = {
                    settings: {},
                    config: config,
                };
                data.settings[column.field] = value;
                api.save(row.breakdownId, data).then(
                    function(breakdown) {
                        extendMetaData(breakdown, metaData);
                        deferred.resolve(breakdown);
                    },
                    function(err) {
                        deferred.reject(err);
                    }
                );

                if (metaData.breakdown === constants.breakdown.AD_GROUP) {
                    return chainNavigationServiceUpdate(
                        row.breakdownId,
                        deferred.promise
                    );
                }
                return deferred.promise;
            };

            this.editRow = function(row) {
                return api.edit(row.id);
            };

            // PRIVATE FUNCTIONS //

            function extendPagination(breakdown) {
                breakdown.pagination.complete =
                    breakdown.pagination.offset + breakdown.pagination.limit ===
                    breakdown.pagination.count;
            }

            function chainNavigationServiceUpdate(adGroupId, promise) {
                // In case we are changing AdGroup settings, notify Navigation service to reload this AdGroup
                var deferred = $q.defer();
                zemNavigationService.notifyAdGroupReloading(adGroupId, true);
                promise.then(
                    function(data) {
                        zemNavigationService.reloadAdGroup(adGroupId);
                        deferred.resolve(data);
                    },
                    function(data) {
                        zemNavigationService.notifyAdGroupReloading(
                            adGroupId,
                            false
                        );
                        deferred.reject(data);
                    }
                );
                return deferred.promise;
            }

            /* eslint-disable complexity */
            function extendMetaData(breakdown, metaData) {
                if (!breakdown) return;

                if (breakdown.batches) {
                    metaData.ext.batches = breakdown.batches;
                    delete breakdown.batches;
                }

                if (breakdown.currency) {
                    metaData.ext.currency = breakdown.currency;
                    delete breakdown.currency;
                }

                if (breakdown.biddingType) {
                    metaData.ext.biddingType = breakdown.biddingType;
                    delete breakdown.biddingType;
                }

                if (breakdown.bid) {
                    metaData.ext.bid = breakdown.bid;
                    delete breakdown.bid;
                }

                if (breakdown.typeSummaries) {
                    metaData.ext.typeSummaries = breakdown.typeSummaries;
                    delete breakdown.typeSummaries;
                }

                if (breakdown.autopilotState) {
                    metaData.ext.autopilotState = breakdown.autopilotState;
                    delete breakdown.autopilotState;
                }

                if (breakdown.obBlacklistedCount) {
                    metaData.ext.obBlacklistedCount =
                        breakdown.obBlacklistedCount;
                    delete breakdown.obBlacklistedCount;
                }

                metaData.ext.enablingAutopilotSourcesAllowed = true;
                if (breakdown.enablingAutopilotSourcesAllowed !== undefined) {
                    metaData.ext.enablingAutopilotSourcesAllowed =
                        breakdown.enablingAutopilotSourcesAllowed;
                    delete breakdown.enablingAutopilotSourcesAllowed;
                }

                if (breakdown.adGroupAutopilotState !== undefined) {
                    metaData.adGroupAutopilotState =
                        breakdown.adGroupAutopilotState;
                    delete breakdown.adGroupAutopilotState;
                }

                if (breakdown.campaignAutopilot !== undefined) {
                    metaData.campaignAutopilot = breakdown.campaignAutopilot;
                    delete breakdown.campaignAutopilot;
                }
            }
        }

        function createMetaData(level, id, breakdown) {
            // Replace first column type to text and field breakdown name, to solve
            // temporary problems with primary column content in level>1 breakdowns
            // FIXME: find appropriate solution for this problem (special type)
            var breakdownGroups = zemGridEndpointBreakdowns.createBreakdownGroups(
                level,
                breakdown
            );
            var columns = zemGridEndpointColumns.createColumns(
                level,
                getAvailableBreakdowns(breakdownGroups)
            );
            var categories = zemGridEndpointColumns.createCategories(columns);

            return {
                id: id,
                level: level,
                breakdown: breakdown,
                columns: columns,
                categories: categories,
                breakdownGroups: breakdownGroups,
                ext: {}, // extensions placeholder
            };
        }

        function getAvailableBreakdowns(breakdownGroups) {
            // Returns all structural breakdowns (text/query) available in group configuration
            return []
                .concat(
                    breakdownGroups.base.breakdowns,
                    breakdownGroups.structure.breakdowns
                )
                .map(function(breakdown) {
                    return breakdown.query;
                });
        }

        function createEndpoint(metaData) {
            return new EndpointService(metaData);
        }

        return {
            createEndpoint: createEndpoint,
            createMetaData: createMetaData,
        };
    });
