angular
    .module('one.widgets')
    .factory('zemGridEndpointApi', function(
        $q,
        $http,
        zemGridEndpointApiConverter,
        zemUtils
    ) {
        // eslint-disable-line max-len
        //
        // EndpointApi - data retrieval (get) and settings persistence (save)
        //
        function EndpointApi(metaData) {
            this.get = get;
            this.save = save;
            this.edit = edit;

            function get(config) {
                var url = createGetUrl(config);
                var deferred = zemUtils.createAbortableDefer();
                var data = zemGridEndpointApiConverter.convertConfigToApi(
                    config
                );
                var httpConfig = {timeout: deferred.abortPromise};

                $http
                    .post(url, {params: data}, httpConfig)
                    .success(function(response) {
                        var breakdowns = response.data;
                        breakdowns = breakdowns
                            ? breakdowns.map(function(breakdown) {
                                  breakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(
                                      config,
                                      breakdown,
                                      metaData
                                  );
                                  return breakdown;
                              })
                            : [];
                        deferred.resolve(breakdowns);
                    })
                    .error(function(data) {
                        deferred.reject(data);
                    });
                return deferred.promise;
            }

            function save(breakdownId, data) {
                var deferred = $q.defer();
                var url = createSaveUrl(breakdownId);
                var config = angular.copy(data.config); // Save unconverted config used when converting breakdown from api
                data.config = zemGridEndpointApiConverter.convertConfigToApi(
                    data.config
                );
                data.settings = zemGridEndpointApiConverter.convertSettingsToApi(
                    data.settings
                );
                $http
                    .post(url, data)
                    .success(function(response) {
                        var breakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(
                            config,
                            response.data,
                            metaData,
                            true
                        );
                        deferred.resolve(breakdown);
                    })
                    .error(function(data) {
                        if (data && data.data && data.data.errors) {
                            data = convertErrorsFromApi(data.data.errors);
                        } else if (!(data && data.data && data.data.message)) {
                            data = {
                                data: {
                                    message:
                                        'An error occurred. Please try again.',
                                },
                            };
                        }
                        deferred.reject(data);
                    });

                return deferred.promise;
            }

            function edit(rowId) {
                var deferred = $q.defer();
                var url = createEditUrl(rowId);
                $http
                    .post(url)
                    .success(function(response) {
                        deferred.resolve(response);
                    })
                    .error(function(data) {
                        deferred.reject(data);
                    });
                return deferred.promise;
            }

            function convertErrorsFromApi(errors) {
                // FIXME: generalize errors & move to converter
                if (errors.hasOwnProperty('b1_sources_group_cpc_cc')) {
                    errors.cpc_cc = (errors.cpc_cc || []).concat(
                        errors.b1_sources_group_cpc_cc
                    );
                }
                if (errors.hasOwnProperty('b1_sources_group_cpm')) {
                    errors.cpm = (errors.cpm || []).concat(
                        errors.b1_sources_group_cpm
                    );
                }
                if (errors.hasOwnProperty('b1_sources_group_daily_budget')) {
                    errors.daily_budget_cc = (
                        errors.daily_budget_cc || []
                    ).concat(errors.b1_sources_group_daily_budget);
                }
                var result = {
                    cpc: errors.cpc_cc,
                    cpm: errors.cpm,
                    dailyBudget: errors.daily_budget_cc,
                    state: errors.state,
                };

                return result;
            }

            function createGetUrl(config) {
                // e.g. /api/all_accounts/breakdown/account/source/by_day
                // e.g. /api/account/22/breakdown/account/source/by_day
                var baseUrl;
                if (metaData.level === constants.level.ALL_ACCOUNTS) {
                    baseUrl = '/api/all_accounts/breakdown/';
                } else {
                    baseUrl =
                        '/api/' +
                        metaData.level +
                        '/' +
                        metaData.id +
                        '/breakdown/';
                }
                var queries = config.breakdown.map(function(breakdown) {
                    return breakdown.query;
                });
                return baseUrl + queries.join('/') + '/';
            }

            function createSaveUrl(breakdownId) {
                // e.g. /api/grid/ad_groups/123/settings
                // e.g. /api/grid/ad_groups/123/sources/33/settings
                var levelKey = metaData.level;
                var breakdownKey = metaData.breakdown + 's';

                if (
                    metaData.breakdown === constants.breakdown.MEDIA_SOURCE ||
                    metaData.breakdown === constants.breakdown.PUBLISHER
                ) {
                    return (
                        '/api/grid/' +
                        levelKey +
                        '/' +
                        metaData.id +
                        '/' +
                        breakdownKey +
                        '/' +
                        breakdownId +
                        '/settings/'
                    );
                }

                return (
                    '/api/grid/' +
                    breakdownKey +
                    '/' +
                    breakdownId +
                    '/settings/'
                );
            }

            function createEditUrl(rowId) {
                var breakdownKey = metaData.breakdown + 's';

                return '/api/grid/' + breakdownKey + '/' + rowId + '/edit/';
            }
        }

        return {
            createInstance: function(metaData) {
                return new EndpointApi(metaData);
            },
        };
    });
