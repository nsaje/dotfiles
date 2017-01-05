/* globals angular,constants,options,moment */
/* eslint-disable camelcase */
'use strict';

angular.module('one.legacy').factory('api', function ($http, $q, zemDataFilterService, zemPermissions) {
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

    function processResponse (resp) {
        return resp.data.success ? resp.data.data : null;
    }

    function addFilteredSources (params) {
        var filteredSources = zemDataFilterService.getFilteredSources();
        if (filteredSources.length > 0) {
            params.filtered_sources = filteredSources.join(',');
        }
    }

    function addAgencyFilter (params) {
        var filteredAgencies = zemDataFilterService.getFilteredAgencies();
        if (filteredAgencies.length > 0) {
            params.filtered_agencies = filteredAgencies;
        }
    }

    function addAccountTypeFilter (params) {
        var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
        if (filteredAccountTypes.length > 0) {
            params.filtered_account_types = filteredAccountTypes;
        }
    }

    function addShowBlacklistedPublisher (params) {
        var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();
        if (filteredPublisherStatus) {
            params.show_blacklisted_publishers = filteredPublisherStatus;
        }
    }

    function Navigation () {

        function convertFromApi (models) {
            if (models.hasOwnProperty('ad_group')) {
                models.adGroup = models.ad_group;
                delete models.ad_group;
            }

            if (models.hasOwnProperty('accounts_count')) {
                models.accountsCount = models.accounts_count;
                delete models.accounts_count;
                models.hasAccounts = models.accountsCount > 0;
            }

            if (models.hasOwnProperty('default_account_id')) {
                models.defaultAccountId = models.default_account_id;
                delete models.default_account_id;
            }


            return models;
        }

        this.getAdGroup = function (id) {
            return this.get('ad_groups/' + id);
        }.bind(this);

        this.getCampaign = function (id) {
            return this.get('campaigns/' + id);
        }.bind(this);

        this.getAccount = function (id) {
            return this.get('accounts/' + id);
        }.bind(this);

        this.getAccountsAccess = function () {
            return this.get('all_accounts');
        }.bind(this);

        this.get = function (route) {
            var deferred = $q.defer();
            var url = '/api/' + route + '/nav/';
            var config = {
                params: {},
            };
            addFilteredSources(config.params);
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http.get(url, config).
                success(function (data) {
                    var resource;

                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(convertFromApi(resource));
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.list = function () {
            var deferred = $q.defer();
            var url = '/api/nav/';
            var config = {
                params: {},
            };
            addFilteredSources(config.params);
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http.get(url, config).
                success(function (data) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource || []);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSources () {
        function convertFromApi (data) {
            var sources = [];
            for (var source, i = 0; i < data.sources.length; i++) {
                source = data.sources[i];
                sources.push({
                    id: source.id,
                    name: source.name,
                    canTargetExistingRegions: source.can_target_existing_regions,
                    canRetarget: source.can_retarget,
                });
            }

            return {
                sources: sources,
                sourcesWaiting: data.sources_waiting
            };
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/sources/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);
            $http.get(url, config).
                success(function (data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.add = function (adGroupId, sourceId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/sources/';

            var data = {
                'source_id': sourceId
            };

            $http.put(url, data).
                success(function (data, status) {
                    deferred.resolve(data);
                }).
                error(function (data, status) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupPublishersState () {
        this.save = function (id, state, level, startDate, endDate, publishersSelected, publishersNotSelected, selectedAll) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/publishers/blacklist/';

            $http.post(url, {
                state: state,
                level: level,
                start_date: startDate,
                end_date: endDate,
                select_all: selectedAll,
                publishers_selected: publishersSelected,
                publishers_not_selected: publishersNotSelected
            }).
                success(function (data) {
                    deferred.resolve(data);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupOverview () {

        this.get = function (id, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/overview/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.header.levelVerbose = data.data.header.level_verbose;
                        data.data.basicSettings = data.data.basic_settings.map(convertFromApi);
                        data.data.performanceSettings = data.data.performance_settings.map(convertFromApi);
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi (setting) {
            setting.detailsLabel = setting.details_label;
            setting.detailsHideLabel = setting.details_hide_label;
            setting.detailsContent = setting.details_content;
            setting.valueClass = setting.value_class;
            return setting;
        }
    }

    function AccountUserAction () {
        this.post = function (accountId, userId, action) {
            var deferred = $q.defer(),
                url = '/api/accounts/' + accountId + '/users/' + userId + '/' + action,
                config = {
                    params: {}
                },
                data = {};

            $http.post(url, config).
                success(function (data, status) {
                    deferred.resolve(data.data);
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });
            return deferred.promise;
        };
    }

    function DailyStats () {
        function convertFromApi (group) {
            return {
                id: group.id,
                name: group.name,
                seriesData: group.series_data
            };
        }

        var breakdownUrlMap = {};
        breakdownUrlMap[constants.breakdown.ACCOUNT] = 'accounts';
        breakdownUrlMap[constants.breakdown.CAMPAIGN] = 'campaigns';
        breakdownUrlMap[constants.breakdown.AD_GROUP] = 'ad_groups';
        breakdownUrlMap[constants.breakdown.CONTENT_AD] = 'contentads';
        breakdownUrlMap[constants.breakdown.MEDIA_SOURCE] = 'sources';

        this.listPublishersStats = function (id, startDate, endDate, selectedIds, totals, metrics) {
            var url = '/api/ad_groups/' + id + '/publishers/daily_stats/';
            return getData(url, startDate, endDate, metrics, selectedIds, totals);
        };

        this.list = function (level, id, breakdown, startDate, endDate, selection, totals, metrics) {
            var url = '/api/' + level + (id ? ('/' + id) : '') + '/' + breakdownUrlMap[breakdown] + '/daily_stats/';
            return getData(url, startDate, endDate, metrics, selection, totals);
        };

        function getData (url, startDate, endDate, metrics, selection, totals) {
            var deferred = createAbortableDefer();
            var config = {
                params: {},
                timeout: deferred.abortPromise,
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (selection.selectedIds) {
                config.params.selected_ids = selection.selectedIds;
            }

            if (totals) {
                config.params.totals = totals;
            }

            if (metrics) {
                config.params.metrics = metrics;
            }

            if (selection.selectAll) {
                config.params.select_all = selection.selectAll;
            }

            if (selection.unselectedIds) {
                config.params.not_selected_ids = selection.unselectedIds;
            }

            if (selection.batchId) {
                config.params.select_batch = selection.batchId;
            }

            addFilteredSources(config.params);
            addShowBlacklistedPublisher(config.params);

            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http.get(url, config).
                success(function (response, status) {
                    var chartData, conversionGoals, pixels;
                    if (response && response.data) {
                        if (response.data.chart_data) {
                            chartData = {
                                groups: response.data.chart_data.map(function (group) {
                                    return convertFromApi(group);
                                }),
                                campaignGoals: response.data.campaign_goals,
                                goalFields: response.data.goal_fields,
                            };
                        }
                        if (response.data.conversion_goals) {
                            conversionGoals = response.data.conversion_goals;
                        }
                        if (response.data.pixels) {
                            pixels = response.data.pixels;
                        }
                    }
                    deferred.resolve({
                        chartData: chartData,
                        conversionGoals: conversionGoals,
                        pixels: pixels,
                    });
                }).
                error(function (data, status, headers, config) {
                    if (status === -1) { // request was aborted, do nothing
                        return;
                    }
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    }

    function CampaignOverview () {

        this.get = function (id, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/overview/';
            var config = {
                params: {}
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.header.levelVerbose = data.data.header.level_verbose;
                        data.data.basicSettings = data.data.basic_settings.map(convertFromApi);
                        data.data.performanceSettings = data.data.performance_settings.map(convertFromApi);
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi (setting) {
            setting.detailsLabel = setting.details_label;
            setting.detailsHideLabel = setting.details_hide_label;
            setting.detailsContent = setting.details_content;
            setting.valueClass = setting.value_class;
            return setting;
        }
    }

    function CampaignContentInsights () {
        this.get = function (id, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/content-insights/';
            var config = {
                params: {},
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        var convertedData = {
                            metric: data.data.metric,
                            summary: data.data.summary,
                            bestPerformerRows: data.data.best_performer_rows,
                            worstPerformerRows: data.data.worst_performer_rows,
                        };
                        deferred.resolve(convertedData);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function History () {
        function convertHistoryFromApi (history) {
            return history.map(function (item) {
                return {
                    changedBy: item.changed_by,
                    changesText: item.changes_text,
                    datetime: item.datetime,
                };
            });
        }

        function convertFilterToApi (filter) {
            return {
                ad_group: filter.adGroup,
                campaign: filter.campaign,
                account: filter.account,
                agency: filter.agency,
                level: filter.level,
            };
        }

        this.get = function (filter, order) {
            var deferred = $q.defer();
            var url = '/api/history/';
            var config = {
                params: convertFilterToApi(filter),
            };

            if (order) {
                config.params.order = order
                    .replace('changedBy', 'created_by')
                    .replace('datetime', 'created_dt');
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        history: convertHistoryFromApi(data.data.history),
                    });
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountOverview () {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/overview/';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.header.levelVerbose = data.data.header.level_verbose;
                        data.data.basicSettings = data.data.basic_settings.map(convertFromApi);
                        data.data.performanceSettings = data.data.performance_settings.map(convertFromApi);
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi (setting) {
            setting.detailsLabel = setting.details_label;
            setting.detailsHideLabel = setting.details_hide_label;
            setting.detailsContent = setting.details_content;
            return setting;
        }
    }

    function AllAccountsOverview () {

        this.get = function (startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/accounts/overview/';
            var config = {
                params: {},
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http.get(url, config).
                success(function (data) {
                    if (data && data.data) {
                        data.data.header.levelVerbose = data.data.header.level_verbose;
                        data.data.basicSettings = data.data.basic_settings.map(convertFromApi);
                        if (data.data.performanceSettings) {
                            data.data.performanceSettings = data.data.performance_settings.map(convertFromApi);
                        }
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi (setting) {
            setting.detailsLabel = setting.details_label;
            setting.detailsHideLabel = setting.details_hide_label;
            setting.detailsContent = setting.details_content;
            return setting;
        }
    }

    function ScheduledReports () {
        this.get = function (level, id) {
            var deferred = $q.defer();
            var url;
            if (level === constants.level.ALL_ACCOUNTS) {
                url = '/api/all_accounts/reports/';
            } else if (level === constants.level.ACCOUNTS) {
                url = '/api/accounts/' + id + '/reports/';
            } else {
                return;
            }
            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve(data.data);
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.removeReport = function (scheduledReportId) {
            var deferred = $q.defer();
            var url = '/api/accounts/reports/remove/' + scheduledReportId;
            $http.delete(url).
                success(function (data, status) {
                    if (status != 200) {
                        deferred.reject(data);
                    }
                    deferred.resolve();
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.addScheduledReport = function (url, data) {
            var deferred = $q.defer();
            $http.put(url, data).
                success(function (data, status) {
                    if (status != 200) {
                        deferred.reject(data);
                    }
                    deferred.resolve();
                }).
                error(function (data, status) {
                    var errors = null;
                    if (data.data && data.data.errors) {
                        errors = data.data.errors;
                    }
                    return deferred.reject(errors);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroupsExportAllowed () {
        function convertFromApi (data) {
            return {
                allowed: data.allowed,
                maxDays: data.max_days
            };
        }

        this.get = function (campaignId, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + campaignId + '/ad_groups/export/allowed/';

            var config = {
                params: {}
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }
            $http.get(url, config).
                success(function (data, status) {
                    var resource;

                    if (data && data.data) {
                        resource = convertFromApi(data.data);
                    }

                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAdsExportAllowed () {
        function convertFromApi (data) {
            return {
                allowed: data.allowed,
                maxDays: data.max_days
            };
        }

        this.get = function (adGroupId, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/export/allowed/';

            var config = {
                params: {}
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            $http.get(url, config).
                success(function (data, status) {
                    var resource;

                    if (data && data.data) {
                        resource = convertFromApi(data.data);
                    }

                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function ExportAllowed () {
        function convertFromApi (data) {
            return {
                content_ad: data.content_ad,
                ad_group: data.ad_group,
                campaign: data.campaign,
                account: data.account,
                all_accounts: data.all_accounts,
                byDay: {
                    content_ad: data.by_day.content_ad,
                    ad_group: data.by_day.ad_group,
                    campaign: data.by_day.campaign,
                    account: data.by_day.account,
                    all_accounts: data.by_day.all_accounts
                }
            };
        }

        this.get = function (id_, level_, exportSources, startDate, endDate) {
            var deferred = $q.defer();

            var filteredSources = zemDataFilterService.getFilteredSources();
            var urlId = ((level_ == constants.level.ALL_ACCOUNTS) ? '' : id_ + '/');
            var urlSources = ((exportSources.valueOf()) ? 'sources/' : '');
            var urlFilteredSources = ((exportSources.valueOf()) ? '?filtered_sources=' + filteredSources.join(',') : '');
            var url = '/api/' + level_ + '/' + urlId + urlSources + 'export/allowed/' + urlFilteredSources;

            var config = {
                params: {}
            };
            if (startDate) {
                config.params.start_date = startDate.format();
            }
            if (endDate) {
                config.params.end_date = endDate.format();
            }
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    var resource;

                    if (data && data.data) {
                        resource = convertFromApi(data.data);
                    }

                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function ConversionPixel () {
        function convertFromApi (conversionPixel) {
            return {
                id: conversionPixel.id,
                name: conversionPixel.name,
                url: conversionPixel.url,
                archived: conversionPixel.archived,
                audienceEnabled: conversionPixel.audience_enabled,
            };
        }

        this.list = function (accountId, audienceEnabledOnly) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';
            if (audienceEnabledOnly) {
                url = url + '?audience_enabled_only=1';
            }

            $http.get(url).
                success(function (data, status) {
                    var ret = {
                        rows: data.data.rows.map(convertFromApi),
                        conversionPixelTagPrefix: data.data.conversion_pixel_tag_prefix
                    };

                    deferred.resolve(ret);
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };

        this.post = function (accountId, name, audienceEnabled) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';
            var config = {
                name: name,
                audience_enabled: audienceEnabled,
            };

            $http.post(url, config).
                success(function (data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data, status) {
                    var ret = null;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        ret = data.data;
                    }

                    deferred.reject(ret);
                });

            return deferred.promise;
        };

        this.put = function (conversionPixelId, data) {
            var deferred = $q.defer();
            var url = '/api/conversion_pixel/' + conversionPixelId + '/';

            $http.put(url, data).
                success(function (data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data, status) {
                    var ret = null;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        ret = data.data;
                    }

                    deferred.reject(ret);
                });

            return deferred.promise;
        };

        this.edit = function (conversionPixel) {
            var data = {
                name: conversionPixel.name,
                audience_enabled: conversionPixel.audienceEnabled,
            };

            return this.put(conversionPixel.id, data);
        };

        this.archive = function (conversionPixel) {
            var data = {
                archived: true,
                name: conversionPixel.name
            };

            return this.put(conversionPixel.id, data);
        };

        this.restore = function (conversionPixel) {
            var data = {
                archived: false,
                name: conversionPixel.name
            };

            return this.put(conversionPixel.id, data);
        };
    }

    // Helpers

    function AccountCredit () {
        var self = this;
        this.convert = {
            dataFromApi: function (obj) {
                return {
                    createdBy: obj.created_by,
                    createdOn: obj.created_on && moment(obj.created_on,
                                                        'YYYY-MM-DD').format('MM/DD/YYYY'),
                    startDate: obj.start_date && moment(obj.start_date,
                                                        'YYYY-MM-DD').format('MM/DD/YYYY'),
                    endDate: obj.end_date && moment(obj.end_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                    isSigned: obj.is_signed,
                    isCanceled: obj.is_canceled,
                    account: obj.account_id,
                    licenseFee: obj.license_fee,
                    flatFee: obj.flat_fee,
                    total: obj.total,
                    comment: obj.comment,
                    allocated: obj.allocated,
                    available: obj.available,
                    amount: obj.amount,
                    isAgency: obj.is_agency,
                    budgets: (obj.budgets || []).map(function (itm) {
                        return {
                            id: itm.id,
                            startDate: moment(itm.start_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                            endDate: moment(itm.end_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                            total: itm.total,
                            spend: itm.spend,
                            comment: itm.comment,
                            campaign: itm.campaign
                        };
                    }),
                    numOfBudgets: (obj.budgets || []).length,
                    id: obj.id
                };
            },
            dataToApi: function (obj) {
                return {
                    start_date: obj.startDate && moment(obj.startDate).format('YYYY-MM-DD'),
                    end_date: obj.endDate && moment(obj.endDate).format('YYYY-MM-DD'),
                    amount: obj.amount,
                    license_fee: obj.licenseFee,
                    comment: obj.comment,
                    account: obj.account,
                    is_signed: obj.isSigned,
                    is_agency: obj.isAgency,
                };
            },
            errors: function (resp) {
                return {
                    startDate: resp.data.data.errors.start_date,
                    endDate: resp.data.data.errors.end_date,
                    amount: resp.data.data.errors.amount,
                    licenseFee: resp.data.data.errors.license_fee,
                    comment: resp.data.data.errors.comment,
                    status: resp.data.data.errors.__all__,
                };
            }
        };

        this.list = function (accountId) {
            var url = '/api/accounts/' + accountId + '/credit/';
            return $http.get(url).then(processResponse).then(function (data) {
                if (data === null) { return null; }
                return {
                    active: data.active.map(self.convert.dataFromApi),
                    past: data.past.map(self.convert.dataFromApi),
                    totals: data.totals
                };
            });
        };

        this.create = function (accountId, item) {
            var url = '/api/accounts/' + accountId + '/credit/';
            return $http.put(url, self.convert.dataToApi(item)).then(processResponse);
        };

        this.save = function (accountId, item) {
            var url = '/api/accounts/' + accountId + '/credit/' + item.id + '/';
            return $http.post(url, self.convert.dataToApi(item)).then(processResponse);
        };

        this.get = function (accountId, itemId) {
            var url = '/api/accounts/' + accountId + '/credit/' + itemId + '/';
            return $http.get(url).then(processResponse).then(self.convert.dataFromApi);
        };

        this.delete = function (accountId, itemId) {
            var url = '/api/accounts/' + accountId + '/credit/' + itemId + '/';
            return $http.delete(url).then(processResponse).then(self.convert.dataFromApi);
        };

        this.cancel = function (accountId, itemIds) {
            var url = '/api/accounts/' + accountId + '/credit/';
            return $http.post(url, {
                'cancel': itemIds
            }).then(processResponse);
        };
    }

    function CampaignBudget () {
        var self = this;
        this.convert = {
            dataFromApi: function (obj) {
                return {
                    id: obj.id,
                    credit: obj.credit,
                    amount: obj.amount,
                    startDate: moment(obj.start_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                    endDate: moment(obj.end_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                    total: obj.total || obj.amount,
                    licenseFee: obj.license_fee,
                    createdBy: obj.created_by,
                    createdOn: moment(obj.created_at).format('MM/DD/YYYY'),
                    spend: obj.spend,
                    state: obj.state,
                    isEditable: obj.is_editable,
                    isUpdatable: obj.is_updatable,
                    available: obj.available,
                    margin: obj.margin,
                    comment: obj.comment
                };
            },
            dataToApi: function (obj) {
                return {
                    credit: obj.credit.id,
                    amount: obj.amount,
                    start_date: moment(obj.startDate).format('YYYY-MM-DD'),
                    end_date: moment(obj.endDate).format('YYYY-MM-DD'),
                    margin: obj.margin,
                    comment: obj.comment
                };
            },
            error: function (resp) {
                if (!resp.data.data.errors) { return null; }
                return {
                    amount: resp.data.data.errors.amount,
                    startDate: resp.data.data.errors.start_date,
                    endDate: resp.data.data.errors.end_date,
                    margin: resp.data.data.errors.margin,
                    comment: resp.data.data.errors.comment,
                    credit: resp.data.data.errors.credit
                };
            }
        };

        this.list = function (campaignId) {
            var url = '/api/campaigns/' + campaignId + '/budget/';
            return $http.get(url).then(processResponse).then(function (data) {
                if (data === null) {
                    return null;
                }
                return {
                    active: data.active.map(self.convert.dataFromApi),
                    past: data.past.map(self.convert.dataFromApi),
                    totals: {
                        currentAvailable: data.totals.current.available,
                        currentUnallocated: data.totals.current.unallocated,
                        lifetimeCampaignSpend: data.totals.lifetime.campaign_spend,
                        lifetimeMediaSpend: data.totals.lifetime.media_spend,
                        lifetimeDataSpend: data.totals.lifetime.data_spend,
                        lifetimeLicenseFee: data.totals.lifetime.license_fee,
                        lifetimeMargin: data.totals.lifetime.margin,
                    },
                    credits: data.credits.map(function (obj) {
                        return {
                            licenseFee: obj.license_fee,
                            total: obj.total,
                            available: obj.available,
                            startDate: moment(obj.start_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                            endDate: moment(obj.end_date, 'YYYY-MM-DD').format('MM/DD/YYYY'),
                            id: obj.id,
                            comment: obj.comment,
                            isAvailable: obj.is_available,
                            isAgency: obj.is_agency,
                        };
                    }),
                    minAmount: data.min_amount,
                };
            });
        };

        this.create = function (campaignId, budget) {
            var url = '/api/campaigns/' + campaignId + '/budget/';
            return $http.put(url, self.convert.dataToApi(budget)).then(processResponse);
        };

        this.save = function (campaignId, budget) {
            var url = '/api/campaigns/' + campaignId + '/budget/' + budget.id + '/';
            return $http.post(
                url,
                self.convert.dataToApi(budget)
            ).then(processResponse).then(function (data) {
                return {
                    id: data.id,
                    stateChanged: data.state_changed,
                };
            });
        };

        this.get = function (campaignId, budgetId) {
            var url = '/api/campaigns/' + campaignId + '/budget/' + budgetId + '/';
            return $http.get(url).then(processResponse).then(self.convert.dataFromApi);
        };

        this.delete = function (campaignId, budgetId) {
            var url = '/api/campaigns/' + campaignId + '/budget/' + budgetId + '/';
            return $http.delete(url).then(processResponse).then(self.convert.dataFromApi);
        };
    }

    function CampaignGoalValidation () {
        var self = this;

        self.convert = {
            dataToApi: function (goal) {
                var data = {
                    type: goal.type,
                    value: goal.value,
                    id: goal.id,
                };
                if (goal.conversionGoal) {
                    data.conversion_goal = {
                        goal_id: goal.conversionGoal.goalId,
                        name: goal.conversionGoal.name,
                        type: goal.conversionGoal.type,
                        conversion_window: goal.conversionGoal.conversionWindow,
                    };
                }
                return data;
            },
            dataFromApi: function (data) {
                var goal = data.data;

                if (goal && goal.conversion_goal) {
                    return {
                        conversionGoal: {
                            name: goal.conversion_goal.name,
                            type: goal.conversion_goal.type,
                            conversionWindow: goal.conversion_goal.conversion_window,
                            goalId: goal.conversion_goal.goal_id,
                        }
                    };
                }

                return {};
            },
            errorsFromApi: function (data) {
                var result = {};
                var errors = data.data.errors;

                if (errors.conversion_goal) {
                    result.conversionGoal = {
                        goalId: errors.conversion_goal.goal_id,
                        name: errors.conversion_goal.name,
                        type: errors.conversion_goal.type,
                        conversionWindow: errors.conversion_goal.conversion_window
                    };
                }
                return result;
            }
        };

        self.post = function (campaignId, goal) {
            var url = '/api/campaigns/' + campaignId + '/goals/validate/';
            var deferred = $q.defer();

            $http.post(url, self.convert.dataToApi(goal)).
                success(function (data) {
                    deferred.resolve(self.convert.dataFromApi(data));
                }).
                error(function (data) {
                    deferred.reject(self.convert.errorsFromApi(data));
                });

            return deferred.promise;
        };
    }

    function CustomAudiences () {
        function convertFromApi (data) {
            var resource = {};

            if (data && data.data) {
                resource.id = data.data.id;
                resource.name = data.data.name;
                resource.pixelId = data.data.pixel_id;
                resource.ttl = data.data.ttl;
                resource.rules = [];

                if (!data.data.rules) {
                    return resource;
                }

                for (var i = 0; i < data.data.rules.length; i++) {
                    resource.rules.push({
                        id: data.data.rules[i].id,
                        type: data.data.rules[i].type,
                        value: data.data.rules[i].value,
                    });
                }
            }

            return resource;
        }

        function convertValidationErrorFromApi (errors) {
            var result = {
                name: errors.name,
                pixelId: errors.pixel_id,
                rules: errors.rules,
                ttl: errors.ttl,
            };

            return result;
        }

        this.get = function (accountId, audienceId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/' + audienceId + '/';

            $http.get(url).
                success(function (data) {
                    var resource = convertFromApi(data);
                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.list = function (accountId, includeArchived, includeSize) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/';

            var config = {
                params: {}
            };

            if (includeArchived) {
                config.params.include_archived = '1';
            }

            if (includeSize) {
                config.params.include_size = '1';
            }

            $http.get(url, config).
                success(function (data) {
                    var resource = [];

                    if (data && data.data) {
                        for (var i = 0; i < data.data.length; i++) {
                            resource.push({
                                id: data.data[i].id,
                                name: data.data[i].name,
                                count: data.data[i].count,
                                countYesterday: data.data[i].count_yesterday,
                                archived: data.data[i].archived,
                                createdDt: moment(data.data[i].created_dt).toDate(),
                            });
                        }
                    }

                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.post = function (accountId, audience) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/';

            $http.post(url, audience).
                success(function (data, status) {
                    var resource = convertFromApi(data);
                    deferred.resolve(resource);
                }).
                error(function (data, status) {
                    var ret = null;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        ret = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(ret);
                });

            return deferred.promise;
        };

        this.put = function (accountId, audienceId, audience) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/' + audienceId + '/';

            $http.put(url, audience).
                success(function (data, status) {
                    var resource = convertFromApi(data);
                    deferred.resolve(resource);
                }).
                error(function (data, status) {
                    var ret = null;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        ret = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(ret);
                });

            return deferred.promise;
        };
    }

    function CustomAudiencesArchive () {
        this.archive = function (accountId, audienceId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/' + audienceId + '/archive/';
            var config = {
                params: {}
            };

            var data = {};

            $http.post(url, data, config).
                success(function (data, status) {
                    deferred.resolve();
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.restore = function (accountId, audienceId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/' + audienceId + '/restore/';

            var config = {
                params: {}
            };

            var data = {};

            $http.post(url, data, config).
                success(function (data, status) {
                    deferred.resolve();
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    return {
        campaignContentInsights: new CampaignContentInsights(),
        scheduledReports: new ScheduledReports(),
        accountUserAction: new AccountUserAction(),
        exportAllowed: new ExportAllowed(),
        adGroupAdsExportAllowed: new AdGroupAdsExportAllowed(),
        campaignAdGroupsExportAllowed: new CampaignAdGroupsExportAllowed(),
        conversionPixel: new ConversionPixel(),
        accountCredit: new AccountCredit(),
        campaignBudget: new CampaignBudget(),
        campaignGoalValidation: new CampaignGoalValidation(),
        customAudiences: new CustomAudiences(),
        customAudiencesArchive: new CustomAudiencesArchive(),

        // TODO: refactor - chart component
        dailyStats: new DailyStats(),

        // TODO: refactor - navigation service endpoint
        navigation: new Navigation(),

        // TODO: refactor - history service endpoint
        history: new History(),

        // TODO: refactor - infobox/overview component endpoint
        allAccountsOverview: new AllAccountsOverview(),
        accountOverview: new AccountOverview(),
        adGroupOverview: new AdGroupOverview(),
        campaignOverview: new CampaignOverview(),

        // TODO: refactor - services
        adGroupSources: new AdGroupSources(),
        adGroupPublishersState: new AdGroupPublishersState(),
    };
});
