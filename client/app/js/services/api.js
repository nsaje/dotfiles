/*globals angular,oneApp,constants,options,moment*/
"use strict";

angular.module('oneApi', []).factory("api", ["$http", "$q", function($http, $q) {
    function NavData() {
        this.list = function () {
            var deferred = $q.defer();
            var url = '/api/nav_data';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    } 

    function User() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/users/' + id + '/';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data.user;
                    }
                    deferred.resolve(resource);
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSources() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/sources/';

            $http.get(url).
                success(function (data, status) {
                    deferred.resolve({
                        sources: data.data.sources,
                        sourcesWaiting: data.data.sources_waiting
                    });
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
        }
    }

    function AdGroupSourcesTable() {
        this.get = function (id, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/sources/table/';
            var config = {
                params: {}
            };

            config.params.order = order;

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAdsTable() {
        this.get = function (id, page, size, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/contentads/table/';
            var config = {
                params: {}
            };

            if (page) {
                config.params.page = page;
            }

            if (size) {
                config.params.size = size;
            }

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (order) {
                config.params.order = order;
            }

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSync() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/sync/';

            $http.get(url).
                success(function (data, status) {
                    var resource;
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckSyncProgress() {
        this.get = function(id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/check_sync_progress/';

            $http.get(url).
                success(function(data, status){
                    var resource;
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountSync() {
        this.get = function () {
            var deferred = $q.defer();
            var url = '/api/accounts/sync/';

            $http.get(url).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckAccountsSyncProgress() {
        this.get = function(id) {
            var deferred = $q.defer();
            var url = '/api/accounts/check_sync_progress/';

            $http.get(url).
                success(function(data, status){
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckCampaignSyncProgress() {
        this.get = function(id) {
            var deferred = $q.defer(id);
            var url = '/api/campaigns/' + id + '/check_sync_progress/';

            $http.get(url).
                success(function(data, status){
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupDailyStats() {
        function convertFromApi(data) {
            data.date = parseInt(moment.utc(data.date).format('XSSS'));
            data.sourceId = data.source_id;
            data.sourceName = data.source_name;
            return data;
        }

        this.list = function (adGroupId, startDate, endDate, sourceIds, totals) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/daily_stats/';
            var config = {
                params: {}
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (sourceIds) {
                config.params.source_ids = sourceIds;
            }

            if (totals) {
                config.params.totals = totals;
            }

            $http.get(url, config).
                success(function (response, status) {
                    var stats, options;
                    if (response && response.data && response.data.stats) {
                        stats = response.data.stats;
                        stats = response.data.stats.map(function (x) {
                            return convertFromApi(x);
                        });
                    }
                    if (response && response.data && response.data.options) {
                        options = response.data.options;
                    }
                    deferred.resolve({
                        stats: stats,
                        options: options
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function DailyStats() {
        function convertFromApi(group) {
            return {
                id: group.id,
                name: group.name,
                seriesData: group.series_data
            };
        }

        this.list = function (modelName, id, startDate, endDate, selectedIds, totals, metric1, metric2) {
            var deferred = $q.defer();
            var url = '/api/' + modelName + '/' + id + '/daily_stats/';
            var config = {
                params: { metrics: [] }
            };
            var metrics;

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (selectedIds) {
                config.params.selected_ids = selectedIds;
            }

            if (totals) {
                config.params.totals = totals;
            }

            if (metric1) {
                config.params.metrics.push(metric1);
            }

            if (metric2) {
                config.params.metrics.push(metric2);
            }

            $http.get(url, config).
                success(function (response, status) {
                    var chartData, goals;
                    if (response && response.data && response.data.chart_data) {
                        chartData = response.data.chart_data.map(function (group) {
                            return convertFromApi(group);
                        });
                    }
                    if (response && response.data && response.data.goals) {
                        goals = response.data.goals;
                    }
                    deferred.resolve({
                        chartData: chartData,
                        goals: goals
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupState() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/state/';

            $http.get(url).
                success(function (data, status) {
                    var resource;
                    if (data && data.data && data.data.state) {
                        resource = data.data.state;
                    }
                    deferred.resolve({
                        state: resource,
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSettings() {
        function convertFromApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                state: settings.state,
                startDate: settings.start_date ? new Date(settings.start_date) : null,
                endDate: settings.end_date ? new Date(settings.end_date) : null,
                manualStop: !settings.end_date,
                cpc: settings.cpc_cc,
                dailyBudget: settings.daily_budget_cc,
                targetDevices: options.adTargetDevices.map(function (item) {
                    var device = {
                        name: item.name,
                        value: item.value,
                        checked: false
                    };

                    if (settings.target_devices && settings.target_devices.indexOf(item.value) > -1) {
                        device.checked = true;
                    }

                    return device;
                }),
                targetRegionsMode: settings.target_regions && settings.target_regions.length ? 'custom' : 'worldwide',
                targetRegions: settings.target_regions,
                trackingCode: settings.tracking_code
            };
        }

        function convertToApi(settings) {
            var targetDevices = [];
            settings.targetDevices.forEach(function (item) {
                if (item.checked) {
                    targetDevices.push(item.value);
                }
            });

            var result = {
                id: settings.id,
                name: settings.name,
                state: parseInt(settings.state, 10),
                start_date: settings.startDate ? moment(settings.startDate).format('YYYY-MM-DD') : null,
                end_date: settings.endDate ? moment(settings.endDate).format('YYYY-MM-DD') : null,
                cpc_cc: settings.cpc,
                daily_budget_cc: settings.dailyBudget,
                target_devices: targetDevices,
                target_regions: settings.targetRegionsMode === 'worldwide' ? [] : settings.targetRegions,
                tracking_code: settings.trackingCode
            };

            return result;
        }

        function convertValidationErrorFromApi(errors) {
            var result = {
                name: errors.name,
                state: errors.state,
                startDate: errors.start_date,
                endDate: errors.end_date,
                cpc: errors.cpc_cc,
                dailyBudget: errors.daily_budget_cc,
                targetDevices: errors.target_devices,
                targetRegions: errors.target_regions,
                trackingCode: errors.tracking_code
            };

            return result;
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/settings/';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data && data.data.settings) {
                        resource = convertFromApi(data.data.settings);
                    }
                    deferred.resolve({
                        settings: resource,
                        actionIsWaiting: data.data.action_is_waiting
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + settings.id + '/settings/';
            var config = {
                params: {}
            };

            var data = {
                'settings': convertToApi(settings)
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data && data.data.settings) {
                        resource = convertFromApi(data.data.settings);
                    }
                    deferred.resolve({
                        settings: resource,
                        actionIsWaiting: data.data.action_is_waiting
                    });
                }).
                error(function(data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function AccountAgency() {
        function convertSettingsFromApi(settings) {
            return {
                id: settings.id,
                name: settings.name
            };
        }

        function convertSettingsToApi(settings) {
            return {
                id: settings.id,
                name: settings.name
            };
        }

        function convertValidationErrorFromApi(errors) {
            return {
                id: errors.id,
                name: errors.name
            };
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/agency/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                    });
                }).
                error(function(data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + settings.id + '/agency/';
            var config = {
                params: {}
            };

            var data = {
                'settings': convertSettingsToApi(settings)
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                    });
                }).
                error(function(data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroups() {
        this.create = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/ad_groups/';

            $http.put(url).
                success(function (data, status) {
                    deferred.resolve({
                        name: data.data.name,
                        id: data.data.id
                    });
                }).
                error(function (data, status) {
                    deferred.reject(); 
                });

            return deferred.promise;
        };
    }

    function CampaignSettings() {
        function convertSettingsFromApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                accountManager: settings.account_manager,
                salesRepresentative: settings.sales_representative,
                serviceFee: settings.service_fee,
                IABCategory: settings.iab_category,
                promotionGoal: settings.promotion_goal
            };
        }

        function convertHistoryFromApi(history) {
            return history.map(function (item) {
                return {
                    changedBy: item.changed_by,
                    changesText: item.changes_text,
                    settings: item.settings.map(function (setting) {
                        var value = setting.value,
                            oldValue = setting.old_value;

                        // insert zero-width space in emails for nice word wrapping
                        if (typeof value === 'string') {
                            value = value.replace('@', '&#8203;@');
                        }

                        if (typeof oldValue === 'string') {
                            oldValue = oldValue.replace('@', '&#8203;@');
                        }
                        
                        return {
                            name: setting.name,
                            value: value,
                            oldValue: oldValue
                        };
                    }),
                    datetime: item.datetime,
                    showOldSettings: item.show_old_settings
                };
            }); 
        }

        function convertSettingsToApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                account_manager: settings.accountManager,
                sales_representative: settings.salesRepresentative,
                service_fee: settings.serviceFee,
                iab_category: settings.IABCategory,
                promotion_goal: settings.promotionGoal
            };
        }

        function convertValidationErrorFromApi(errors) {
            var result = {
                id: errors.id,
                name: errors.name,
                accountManager: errors.account_manager,
                salesRepresentative: errors.sales_representative,
                serviceFee: errors.service_fee,
                IABCategory: errors.iab_category,
                promotionGoal: errors.promotion_goal
            };

            return result;
        }


        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/settings/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                        accountManagers: data.data.account_managers,
                        salesReps: data.data.sales_reps,
                        history: convertHistoryFromApi(data.data.history)
                    });
                }).
                error(function(data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + settings.id + '/settings/';
            var config = {
                params: {}
            };

            var data = {
                'settings': convertSettingsToApi(settings)
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                        history: convertHistoryFromApi(data.data.history)
                    });
                }).
                error(function(data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function CampaignSync() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/sync/';

            $http.get(url).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAgency() {
        function convertFromApi(settings) {
            return {
                id: settings.id,
                trackingCode: settings.tracking_code
            };
        }

        function convertToApi(settings) {
            var result = {
                id: settings.id,
                tracking_code: settings.trackingCode
            };

            return result;
        }

        function convertHistoryFromApi(history) {
            return history.map(function (item) {
                return {
                    changedBy: item.changed_by,
                    changesText: item.changes_text,
                    settings: item.settings.map(function (setting) {
                        var value = setting.value,
                            oldValue = setting.old_value;

                        // insert zero-width space in emails for nice word wrapping
                        if (typeof value === 'string') {
                            value = value.replace('@', '&#8203;@');
                        }

                        if (typeof oldValue === 'string') {
                            oldValue = oldValue.replace('@', '&#8203;@');
                        }
                        
                        return {
                            name: setting.name,
                            value: value,
                            oldValue: oldValue
                        };
                    }),
                    datetime: item.datetime,
                    showOldSettings: item.show_old_settings
                };
            }); 
        }

        function convertValidationErrorFromApi(errors) {
            var result = {
                trackingCode: errors.tracking_code
            };

            return result;
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/agency/';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    var settings;
                    var history;
                    if (data && data.data && data.data.settings) {
                        settings = convertFromApi(data.data.settings);
                        history = convertHistoryFromApi(data.data.history);
                    }
                    deferred.resolve({
                        settings: settings,
                        history: history,
                        actionIsWaiting: data.data.action_is_waiting
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + settings.id + '/agency/';
            var config = {
                params: {}
            };

            var data = {
                'settings': convertToApi(settings)
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    var settings;
                    var history;
                    if (data && data.data && data.data.settings) {
                        settings = convertFromApi(data.data.settings);
                        history = convertHistoryFromApi(data.data.history);
                    }
                    deferred.resolve({
                        settings: settings,
                        history: history,
                        actionIsWaiting: data.data.action_is_waiting
                    });
                }).
                error(function(data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function Account() {
        this.create = function () {
            var deferred = $q.defer();
            var url = '/api/accounts/';

            $http.put(url).
                success(function (data, status) {
                    deferred.resolve({
                        name: data.data.name,
                        id: data.data.id
                    });
                }).
                error(function (data, status) {
                    deferred.reject(); 
                });

            return deferred.promise;
        };
    }

    function AccountCampaigns() {
        this.create = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/campaigns/';

            $http.put(url).
                success(function (data, status) {
                    deferred.resolve({
                        name: data.data.name,
                        id: data.data.id
                    });
                }).
                error(function (data, status) {
                    deferred.reject(); 
                });

            return deferred.promise;
        };
    }

    function AccountDailyStats() {
        function convertFromApi(data) {
            var result = {
                date: parseInt(moment.utc(data.date).format('XSSS'), 10),
                clicks: data.clicks,
                impressions: data.impressions,
                ctr: data.ctr !== null ? parseFloat((data.ctr).toFixed(2)) : null,
                cpc: data.cpc !== null ? parseFloat((data.cpc).toFixed(3)) : null,
                cost: data.cost !== null ? parseFloat((data.cost).toFixed(2)) : null
            };
            return result;
        }

        this.list = function (startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/accounts/daily_stats/';
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
                success(function (response, status) {
                    var resource;
                    if (response && response.data && response.data.stats) {
                        resource = response.data.stats;
                        resource = response.data.stats.map(function (x) {
                            return convertFromApi(x);
                        });
                    }
                    deferred.resolve(resource);
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountAccountsTable() {
        this.get = function (page, size, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/accounts/table/';
            var config = {
                params: {}
            };

            if (page) {
                config.params.page = page;
            }

            if (size) {
                config.params.size = size;
            }

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (order) {
                config.params.order = order;
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroupsTable() {
        function convertRowsFromApi(data) {
            var result = data;
            // result.name = {
            //     text: result.name,
            //     url: '/test'
            // };
            result.state_text = result.state === constants.adGroupSettingsState.ACTIVE ? 'Active' : 'Paused';
            return result;
        }

        this.get = function (id, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/ad_groups/table/';
            var config = {
                params: {}
            };

            if (startDate) {
                config.params.start_date = startDate.format();
            }

            if (endDate) {
                config.params.end_date = endDate.format();
            }

            if (order) {
                config.params.order = order;
            }

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        // data.data.rows = data.data.rows.map(function (x) {
                        //     return convertRowsFromApi(x);
                        // });
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function ActionLog() {
        this.list = function (filters) {
            var deferred = $q.defer();
            var url = '/action_log/api/';
            var config = {
                params: {
                    filters: filters
                }
            };

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource);
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save_state = function (action_id, new_state) {
            var deferred = $q.defer();
            var url = '/action_log/api/' + action_id + '/';
            var config = {
                params: {}
            };

            var data = {
                state: new_state
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource);
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    return {
        navData: new NavData(),
        user: new User(),
        adGroupState: new AdGroupState(),
        adGroupSettings: new AdGroupSettings(),
        adGroupAgency: new AdGroupAgency(),
        adGroupSources: new AdGroupSources(),
        adGroupSourcesTable: new AdGroupSourcesTable(),
        adGroupAdsTable: new AdGroupAdsTable(),
        adGroupSync: new AdGroupSync(),
        campaignAdGroups: new CampaignAdGroups(),
        campaignAdGroupsTable: new CampaignAdGroupsTable(),
        campaignSettings: new CampaignSettings(),
        campaignSync: new CampaignSync(),
        accountAgency: new AccountAgency(),
        account: new Account(),
        accountDailyStats: new AccountDailyStats(),
        accountAccountsTable: new AccountAccountsTable(),
        accountCampaigns: new AccountCampaigns(),
        accountSync: new AccountSync(),
        checkAccountsSyncProgress: new CheckAccountsSyncProgress(),
        checkCampaignSyncProgress: new CheckCampaignSyncProgress(),
        checkSyncProgress: new CheckSyncProgress(),
        adGroupDailyStats: new AdGroupDailyStats(),
        dailyStats: new DailyStats(),
        actionLog: new ActionLog()
    };
}]);
