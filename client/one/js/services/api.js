/* globals angular,oneApp,constants,options,moment */
/* eslint-disable camelcase */
'use strict';

oneApp.factory('api', ['$http', '$q', 'zemFilterService', function ($http, $q, zemFilterService) {

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
        if (zemFilterService.getFilteredSources().length > 0) {
            params.filtered_sources = zemFilterService.getFilteredSources().join(',');
        }
    }

    function addShowArchived (params) {
        if (zemFilterService.getShowArchived()) {
            params.show_archived = zemFilterService.getShowArchived();
        }
    }

    function addShowBlacklistedPublisher (params) {
        if (zemFilterService.getBlacklistedPublishers()) {
            params.show_blacklisted_publishers = zemFilterService.getBlacklistedPublishers();
        }
    }

    function convertTargetDevicesFromApi (targetDevices) {
        return options.adTargetDevices.map(function (item) {
            var device = {
                name: item.name,
                value: item.value,
                checked: false,
            };

            if (targetDevices && targetDevices.indexOf(item.value) > -1) {
                device.checked = true;
            }

            return device;
        });
    }

    function convertTargetDevicesToApi (targetDevices) {
        return targetDevices.filter(function (item) {
            return item.checked;
        }).map(function (item) {
            return item.value;
        });
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

    function User () {
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
                    deferred.resolve(convertFromApi(resource));
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi (data) {
            return {
                id: data.id,
                name: data.name,
                email: data.email,
                agency: data.agency,
                permissions: data.permissions,
                timezoneOffset: data.timezone_offset,
            };
        }
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

    function SourcesTable () {
        function convertRow (row) {
            var convertedRow = {};

            for (var field in row) {
                if (field.indexOf('goals') == '0') {
                    convertGoals(row, convertedRow);
                } else if (field === 'status') {
                    convertedRow[field] = row[field];

                    if (row[field] === constants.adGroupSettingsState.ACTIVE) {
                        convertedRow.status = 'Active';
                    } else if (row[field] === constants.adGroupSettingsState.INACTIVE) {
                        convertedRow.status = 'Paused';
                    } else {
                        convertedRow.status = 'N/A';
                    }
                } else {
                    convertedRow[field] = row[field];
                }
            }
            return convertedRow;
        }

        function convertFromApi (data) {
            for (var i = 0; i < data.rows.length; i++) {
                var row = data.rows[i];
                data.rows[i] = convertRow(row);
            }
            data.totals = convertRow(data.totals);
            data.dataStatus = data.data_status;
            data.conversionGoals = data.conversion_goals;

            return data;
        }

        this.get = function (level, id, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = null;
            if (level === 'all_accounts') {
                url = '/api/' + level + '/sources/table/';
            } else {
                url = '/api/' + level + '/' + id + '/sources/table/';
            }

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

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(convertFromApi(data.data));
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSourcesTable () {
        function convertRow (row) {
            var convertedRow = {};

            for (var field in row) {
                if (field === 'goals') {
                    convertGoals(row, convertedRow);
                } else if (field === 'status') {
                    convertedRow[field] = row[field];

                    if (row[field] === constants.adGroupSettingsState.ACTIVE) {
                        convertedRow.status = 'Active';
                    } else if (row[field] === constants.adGroupSettingsState.INACTIVE) {
                        convertedRow.status = 'Paused';
                    } else {
                        convertedRow.status = 'N/A';
                    }
                } else {
                    convertedRow[field] = row[field];
                }
            }
            return convertedRow;
        }

        function convertFromApi (data) {
            for (var i = 0; i < data.rows.length; i++) {
                var row = data.rows[i];
                data.rows[i] = convertRow(row);
            }
            data.totals = convertRow(data.totals);
            data.lastChange = data.last_change;
            data.dataStatus = data.data_status;
            data.conversionGoals = data.conversion_goals;
            data.adGroupAutopilotState = data.ad_group_autopilot_state;

            data.notifications = convertNotifications(data.notifications);

            return data;
        }

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

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(convertFromApi(data.data));
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupPublishersTable () {

        function convertFromApi (data) {
            data.conversionGoals = data.conversion_goals;
            return data;
        }

        this.get = function (id, page, size, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/publishers/table/';
            var config = {
                params: {}
            };

            config.params.order = order;

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

            addFilteredSources(config.params);
            addShowBlacklistedPublisher(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        deferred.resolve(convertFromApi(data.data));
                    }
                }).
                error(function (data, status, headers, config) {
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

    function AdGroupAdsTable () {
        function convertFromApi (row) {
            row.titleLink = {
                text: row.title,
                url: row.url !== '' ? row.url : null,
                destinationUrl: row.redirector_url
            };

            row.urlLink = {
                text: row.url !== '' ? row.url : 'N/A',
                url: row.url !== '' ? row.url : null
            };

            convertGoals(row, row);

            return row;
        }

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

            addFilteredSources(config.params);
            addShowArchived(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        data.data.rows = data.data.rows.map(convertFromApi);
                        data.data.notifications = convertNotifications(data.data.notifications);
                        data.data.lastChange = data.data.last_change;
                        data.data.dataStatus = data.data.data_status;
                        data.data.conversionGoals = data.data.conversion_goals;
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.getUpdates = function (adGroupId, lastChange) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/table/updates/';

            var config = {
                params: {}
            };

            if (lastChange) {
                config.params.last_change = lastChange;
            }

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data) {
                    deferred.resolve(convertUpdatesFromApi(data.data));
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertUpdatesFromApi (data) {
            var notifications = convertNotifications(data.notifications);

            return {
                rows: data.rows,
                lastChange: data.last_change,
                notifications: notifications,
                inProgress: data.in_progress,
                dataStatus: data.data_status
            };
        }

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

    function AdGroupSync () {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/sync/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckSyncProgress () {
        this.get = function (id) {
            var deferred = $q.defer();
            var config = {
                params: {}
            };

            if (id === undefined) {
                deferred.reject();
                return deferred.promise;
            }

            addFilteredSources(config.params);

            var url = '/api/ad_groups/' + id + '/check_sync_progress/';

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckPublisherBlacklistSyncProgress () {
        this.get = function (id) {
            var deferred = $q.defer();
            var config = {
                params: {}
            };

            if (id === undefined) {
                deferred.reject();
                return deferred.promise;
            }

            var url = '/api/ad_groups/' + id + '/publishers/check_sync_progress/';
            $http.get(url, config).
                then(
                    function (response) {
                        var resource;
                        if (response && response.data && response.data.success) {
                            deferred.resolve(response.data);
                        }
                    },
                    function (response) {
                        deferred.reject(response);
                    });

            return deferred.promise;
        };
    }

    function AccountSync () {
        this.get = function () {
            var deferred = $q.defer();
            var url = '/api/accounts/sync/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckAccountsSyncProgress () {
        this.get = function () {
            var deferred = $q.defer();
            var url = '/api/accounts/check_sync_progress/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckCampaignSyncProgress () {
        this.get = function (campaignId, accountId) {
            var deferred = $q.defer();

            if (campaignId === undefined && accountId === undefined) {
                deferred.reject();
                return deferred.promise;
            }

            var url = '/api/campaigns/check_sync_progress/';

            var config = {
                params: {}
            };

            if (campaignId) {
                config.params.campaign_id = campaignId;
            } else if (accountId) {
                config.params.account_id = accountId;
            }

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function UserActivation () {
        this.post = function (accountId, userId) {
            var deferred = $q.defer(),
                url = '/api/accounts/' + accountId + '/users/' + userId + '/activate',
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

        this.listContentAdStats = function (id, startDate, endDate, metrics) {
            var url = '/api/ad_groups/' + id + '/contentads/daily_stats/';
            return getData(url, startDate, endDate, metrics);
        };

        this.listPublishersStats = function (id, startDate, endDate, selectedIds, totals, metrics) {
            var url = '/api/ad_groups/' + id + '/publishers/daily_stats/';
            return getData(url, startDate, endDate, metrics, selectedIds, totals);
        };

        this.list = function (level, id, startDate, endDate, selectedIds, totals, metrics, groupSources) {
            var url = '/api/' + level + (id ? ('/' + id) : '') + '/daily_stats/';
            return getData(url, startDate, endDate, metrics, selectedIds, totals, groupSources);
        };

        function getData (url, startDate, endDate, metrics, selectedIds, totals, groupSources) {

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

            if (selectedIds) {
                config.params.selected_ids = selectedIds;
            }

            if (totals) {
                config.params.totals = totals;
            }

            if (metrics) {
                config.params.metrics = metrics;
            }

            if (groupSources) {
                config.params.sources = groupSources;
            }

            addFilteredSources(config.params);
            addShowBlacklistedPublisher(config.params);

            $http.get(url, config).
                success(function (response, status) {
                    var chartData, conversionGoals;
                    if (response && response.data && response.data.chart_data) {
                        chartData = {
                            groups: response.data.chart_data.map(function (group) {
                                return convertFromApi(group);
                            }),
                            campaignGoals: response.data.campaign_goals,
                            goalFields: response.data.goal_fields,
                        };
                    }
                    if (response && response.data && response.data.conversion_goals) {
                        conversionGoals = response.data.conversion_goals;
                    }
                    deferred.resolve({
                        chartData: chartData,
                        conversionGoals: conversionGoals
                    });
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    }

    function AdGroupSettings () {
        function convertFromApi (settings) {
            return {
                id: settings.id,
                name: settings.name,
                state: settings.state,
                startDate: settings.start_date ? moment(settings.start_date).toDate() : null,
                endDate: settings.end_date ? moment(settings.end_date).toDate() : null,
                manualStop: !settings.end_date,
                cpc: settings.cpc_cc,
                dailyBudget: settings.daily_budget_cc,
                targetDevices: convertTargetDevicesFromApi(settings.target_devices),
                targetRegions: settings.target_regions,
                trackingCode: settings.tracking_code,
                enableGaTracking: settings.enable_ga_tracking,
                enableAdobeTracking: settings.enable_adobe_tracking,
                adobeTrackingParam: settings.adobe_tracking_param,
                autopilotState: settings.autopilot_state,
                autopilotBudget: settings.autopilot_daily_budget,
                retargetingAdGroups: settings.retargeting_ad_groups,
                autopilotMinBudget: settings.autopilot_min_budget,
                autopilotOptimizationGoal: settings.autopilot_optimization_goal,
            };
        }

        function convertToApi (settings) {
            var result = {
                id: settings.id,
                name: settings.name,
                state: parseInt(settings.state, 10),
                start_date: settings.startDate ? moment(settings.startDate).format('YYYY-MM-DD') : null,
                end_date: settings.endDate ? moment(settings.endDate).format('YYYY-MM-DD') : null,
                cpc_cc: settings.cpc,
                daily_budget_cc: settings.dailyBudget,
                target_devices: convertTargetDevicesToApi(settings.targetDevices),
                target_regions: settings.targetRegions,
                tracking_code: settings.trackingCode,
                enable_ga_tracking: settings.enableGaTracking,
                enable_adobe_tracking: settings.enableAdobeTracking,
                adobe_tracking_param: settings.adobeTrackingParam,
                autopilot_state: settings.autopilotState,
                autopilot_daily_budget: settings.autopilotBudget,
                retargeting_ad_groups: settings.retargetingAdGroups,
            };

            return result;
        }

        function convertValidationErrorFromApi (errors) {
            var result = {
                name: errors.name,
                state: errors.state,
                startDate: errors.start_date,
                endDate: errors.end_date,
                cpc: errors.cpc_cc,
                dailyBudget: errors.daily_budget_cc,
                targetDevices: errors.target_devices,
                targetRegions: errors.target_regions,
                trackingCode: errors.tracking_code,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
                enableGaTracking: errors.enable_ga_tracking,
                enableAdobeTracking: errors.enable_adobe_tracking,
                adobeTrackingParam: errors.adobe_tracking_param,
                autopilotState: errors.autopilot_state,
                autopilotBudget: errors.autopilot_daily_budget,
                retargetingAdGroups: errors.retargeting_ad_groups,
            };

            return result;
        }

        function convertDefaultSettingsFromApi (settings) {
            return {
                targetRegions: settings.target_regions,
                targetDevices: convertTargetDevicesFromApi(settings.target_devices),
            };
        }

        function convertRetargetingAdgroupsFromApi (rows) {
            var ret = [];
            for (var id in rows) {
                var row = rows[id];
                ret.push({
                    id: row.id,
                    name: row.name,
                    archived: row.archived,
                    campaignName: row.campaign_name,
                });
            }
            return ret;
        }

        function convertWarningsFromApi (warnings) {
            var ret = {};
            ret.retargeting = warnings.retargeting;
            if (warnings.end_date !== undefined) {
                ret.endDate = {
                    campaignId: warnings.end_date.campaign_id,
                };
            }
            return ret;
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/settings/';
            var config = {
                params: {},
            };

            $http.get(url, config).
                success(function (data) {
                    var settings, defaultSettings, warnings, retargetableAdGroups = [];
                    if (data && data.data && data.data.settings) {
                        settings = convertFromApi(data.data.settings);
                    }
                    if (data && data.data && data.data.default_settings) {
                        defaultSettings = convertDefaultSettingsFromApi(data.data.default_settings);
                    }

                    if (data && data.data && data.data.retargetable_adgroups) {
                        retargetableAdGroups = convertRetargetingAdgroupsFromApi(data.data.retargetable_adgroups);
                    }

                    if (data && data.data && data.data.warnings) {
                        warnings = convertWarningsFromApi(data.data.warnings);
                    }

                    deferred.resolve({
                        settings: settings,
                        defaultSettings: defaultSettings,
                        actionIsWaiting: data.data.action_is_waiting,
                        retargetableAdGroups: retargetableAdGroups,
                        warnings: warnings,
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore,
                    });
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + settings.id + '/settings/';
            var config = {
                params: {},
            };

            var data = {
                'settings': convertToApi(settings),
            };

            $http.put(url, data, config).
                success(function (data) {
                    var settings, defaultSettings;
                    if (data && data.data && data.data.settings) {
                        settings = convertFromApi(data.data.settings);
                    }
                    if (data && data.data && data.data.default_settings) {
                        defaultSettings = convertDefaultSettingsFromApi(data.data.default_settings);
                    }
                    deferred.resolve({
                        settings: settings,
                        defaultSettings: defaultSettings,
                        actionIsWaiting: data.data.action_is_waiting,
                    });
                }).
                error(function (data, status) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function AdGroupSettingsState () {
        this.post = function (adgroupId, state) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adgroupId + '/settings/state/';

            $http.post(url, {state: state}).
                success(function (data, status) {
                    deferred.resolve(data.data);
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupArchive () {
        this.archive = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/archive/';
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

        this.restore = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/restore/';

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

    function CampaignArchive () {
        this.archive = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/archive/';
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

        this.restore = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/restore/';

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

    function AccountArchive () {
        this.archive = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/archive/';
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

        this.restore = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/restore/';

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

    function AccountHistory () {
        function convertHistoryFromApi (history) {
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

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/history/';

            $http.get(url).
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

    function AccountSettings () {
        function convertSettingsFromApi (settings) {
            return {
                id: settings.id,
                name: settings.name,
                defaultAccountManager: settings.default_account_manager,
                defaultSalesRepresentative: settings.default_sales_representative,
                accountType: settings.account_type,
                allowedSources: settings.allowed_sources
            };
        }

        function convertSettingsToApi (settings) {
            return {
                id: settings.id,
                name: settings.name,
                default_account_manager: settings.defaultAccountManager,
                default_sales_representative: settings.defaultSalesRepresentative,
                account_type: settings.accountType,
                allowed_sources: settings.allowedSources
            };
        }

        function convertValidationErrorFromApi (data) {
            return {
                id: data.errors.id,
                name: data.errors.name,
                defaultAccountManager: data.errors.default_account_manager,
                defaultSalesRepresentative: data.errors.default_sales_representative,
                accountType: data.errors.account_type,
                allowedSources: data.errors.allowed_sources,
                allowedSourcesData: data.data.allowed_sources
            };
        }

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/settings/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                        accountManagers: data.data.account_managers,
                        salesReps: data.data.sales_reps,
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore
                    });
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + settings.id + '/settings/';
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
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore,
                    });
                }).
                error(function (data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroups () {
        this.create = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/ad_groups/';

            $http.put(url).
                success(function (data, status) {
                    deferred.resolve({
                        name: data.data.name,
                        id: data.data.id,
                    });
                }).
                error(function (data, status) {
                    deferred.reject();
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

    function CampaignHistory () {
        function convertHistoryFromApi (history) {
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

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/history/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        history: convertHistoryFromApi(data.data.history)
                    });
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CampaignSettings () {
        function convertSettingsFromApi (settings) {
            return {
                id: settings.id,
                name: settings.name,
                campaignGoal: settings.campaign_goal,
                goalQuantity: settings.goal_quantity,
                targetDevices: convertTargetDevicesFromApi(settings.target_devices),
                targetRegions: settings.target_regions,
                campaignManager: settings.campaign_manager,
                IABCategory: settings.iab_category,
            };
        }

        function convertSettingsToApi (settings) {
            return {
                id: settings.id,
                name: settings.name,
                campaign_goal: settings.campaignGoal,
                goal_quantity: settings.goalQuantity,
                target_devices: convertTargetDevicesToApi(settings.targetDevices),
                target_regions: settings.targetRegions,
                campaign_manager: settings.campaignManager,
                iab_category: settings.IABCategory,
            };
        }

        function convertValidationErrorFromApi (errors) {
            var result = {
                name: errors.name,
                campaignGoal: errors.campaign_goal,
                noGoals: errors.no_goals,
                goals: errors.goals,
                goalQuantity: errors.goal_quantity,
                targetDevices: errors.target_devices,
                targetRegions: errors.target_regions,
                campaignManager: errors.campaign_manager,
                IABCategory: errors.iab_category,
            };

            return result;
        }

        function convertCampaignGoalsFromApi (goals) {
            return (goals || []).map(function (goal) {
                var converted = {
                    primary: goal.primary,
                    value: goal.values.length ? goal.values[goal.values.length - 1].value : null,
                    type: goal.type,
                    id: goal.id,
                };
                if (goal.conversion_goal) {
                    converted.conversionGoal = {
                        type: goal.conversion_goal.type,
                        name: goal.conversion_goal.name,
                        goalId: goal.conversion_goal.goal_id,
                        conversionWindow: goal.conversion_goal.conversion_window,
                        pixelUrl: goal.conversion_goal.pixel_url,
                    };
                }
                return converted;
            });
        }

        function convertCampaignGoalsToApi (goals) {
            var data = {};
            goals = goals || {};
            data.primary = goals.primary || null;
            data.modified = goals.modified || {};
            data.removed = goals.removed || [];
            data.added = (goals.added || []).map(function (goal) {
                var converted = {
                    primary: goal.primary,
                    value: goal.value,
                    type: goal.type,
                };
                if (goal.conversionGoal) {
                    converted.conversion_goal =  {
                        goal_id: goal.conversionGoal.goalId,
                        name: goal.conversionGoal.name,
                        type: goal.conversionGoal.type,
                        conversion_window: goal.conversionGoal.conversionWindow,
                    };
                }
                return converted;
            });
            return data;
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
                        goals: convertCampaignGoalsFromApi(data.data.goals),
                        campaignManagers: data.data.campaign_managers,
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore,
                    });
                }).
                error(function (data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (settings, campaignGoals) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + settings.id + '/settings/';
            var config = {
                params: {}
            };

            var data = {
                'settings': convertSettingsToApi(settings),
                'goals': convertCampaignGoalsToApi(campaignGoals)
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve({
                        settings: convertSettingsFromApi(data.data.settings),
                        goals: convertCampaignGoalsFromApi(data.data.goals)
                    });
                }).
                error(function (data, status, headers, config) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }


    function CampaignSync () {
        this.get = function (campaignId, accountId) {
            var deferred = $q.defer();
            var url = '/api/campaigns/sync/';

            var config = {
                params: {}
            };

            if (campaignId) {
                config.params.campaign_id = campaignId;
            } else if (accountId) {
                config.params.account_id = accountId;
            }

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.success) {
                        deferred.resolve();
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupHistory () {

        function convertHistoryFromApi (history) {
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

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/history/';
            var config = {
                params: {}
            };

            $http.get(url, config).
                success(function (data, status) {
                    var history;
                    if (data && data.data) {
                        history = convertHistoryFromApi(data.data.history);
                    }
                    deferred.resolve({
                        history: history,
                    });
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function Account () {
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

    function AccountCampaigns () {
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

    function AccountAccountsTable () {
        function convertFromApi (row) {
            if (row.archived) {
                row.status = 'Archived';
            } else if (row.status === constants.adGroupSettingsState.ACTIVE) {
                row.status = 'Active';
            } else {
                row.status = 'Paused';
            }

            return row;
        }

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

            addShowArchived(config.params);
            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.rows = data.data.rows.map(convertFromApi);
                        data.data.dataStatus = data.data.data_status;
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountCampaignsTable () {
        function convertRowsFromApi (data) {
            var result = data;
            result.state_text = result.state === constants.adGroupSettingsState.ACTIVE ? 'Active' : 'Paused';
            return result;
        }

        this.get = function (id, startDate, endDate, order) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/campaigns/table/';
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

            addShowArchived(config.params);
            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.dataStatus = data.data.data_status;
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroupsTable () {
        function convertRowsFromApi (data) {
            var result = data;
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

            addShowArchived(config.params);
            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    if (data && data.data) {
                        data.data.dataStatus = data.data.data_status;
                        data.data.conversionGoals = data.data.conversion_goals;
                        deferred.resolve(data.data);
                    }
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountUsers () {
        function convertToApi (data) {
            return {
                first_name: data.firstName,
                last_name: data.lastName,
                email: data.email
            };
        }

        function convertValidationErrorFromApi (errors) {
            return {
                firstName: errors.first_name,
                lastName: errors.last_name,
                email: errors.email
            };
        }

        this.list = function (accountId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/';

            $http.get(url).
                success(function (data) {
                    var resource;

                    if (data && data.data) {
                        resource = data.data;
                    }

                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.put = function (accountId, userData) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/';

            var data = convertToApi(userData);

            $http.put(url, data).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve({
                        user: resource.user,
                        created: status === 201
                    });
                }).
                error(function (data, status) {
                    var resource = {};
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource.errors = convertValidationErrorFromApi(data.data.errors);
                        resource.message = data.data.message;
                    }

                    deferred.reject(resource);
                });

            return deferred.promise;
        };

        this.remove = function (accountId, userId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/' + userId + '/';

            $http.delete(url).
                success(function (data) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data.user_id;
                    }
                    deferred.resolve(resource);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSourceSettings () {
        function convertValidationErrorFromApi (errors) {
            var result = {
                cpc: errors.cpc_cc,
                dailyBudget: errors.daily_budget_cc,
                state: errors.state,
            };

            return result;
        }

        this.save = function (adGroupId, sourceId, data) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/sources/' + sourceId + '/settings/';

            $http.put(url, data).
                success(function (data) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource);
                }).
                error(function (data, status) {
                    var resource;
                    if (status === 400 && data && data.data.error_code === 'ValidationError') {
                        resource = convertValidationErrorFromApi(data.data.errors);
                    }
                    deferred.reject(resource);
                });

            return deferred.promise;
        };
    }

    function AdGroupSourcesUpdates () {
        function convertFromApi (data) {
            var notifications;

            if (data.rows) {
                for (var id in data.rows) {
                    var row = data.rows[id];
                    var status = row.status;

                    if (status === constants.adGroupSettingsState.ACTIVE) {
                        status = 'Active';
                    } else if (status === constants.adGroupSettingsState.INACTIVE) {
                        status = 'Paused';
                    } else {
                        status = 'N/A';
                    }

                    row.status = status;
                }
            }

            notifications = convertNotifications(data.notifications);

            return {
                rows: data.rows,
                totals: data.totals,
                lastChange: data.last_change,
                notifications: notifications,
                dataStatus: data.data_status,
                inProgress: data.in_progress
            };
        }

        this.get = function (adGroupId, lastChange) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/sources/table/updates/';

            var config = {
                params: {}
            };

            if (lastChange) {
                config.params.last_change_dt = lastChange;
            }

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data) {
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

            var urlId = ((level_ == constants.level.ALL_ACCOUNTS) ? '':id_ + '/');
            var urlSources = ((exportSources.valueOf()) ? 'sources/':'');
            var urlFilteredSources = ((exportSources.valueOf()) ? '?filtered_sources=' + zemFilterService.getFilteredSources().join(','):'');
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

    function AdGroupAdsUpload () {
        this.getDefaults = function (adGroupId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload/';

            $http.get(url).
                success(function (data) {
                    var result = {};

                    if (data && data.data) {
                        result.status = data.data.status;

                        if (data.data.defaults) {
                            result.defaults = {
                                displayUrl: data.data.defaults.display_url,
                                brandName: data.data.defaults.brand_name,
                                description: data.data.defaults.description,
                                callToAction: data.data.defaults.call_to_action
                            };
                        }
                    }
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;

        };

        this.upload = function (adGroupId, data) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload/';

            var formData = new FormData();
            formData.append('content_ads', data.file);
            formData.append('batch_name', data.batchName ? data.batchName : '');
            formData.append('display_url', data.displayUrl ? data.displayUrl : '');
            formData.append('brand_name', data.brandName ? data.brandName : '');
            formData.append('description', data.description ? data.description : '');
            formData.append('call_to_action', data.callToAction ? data.callToAction : '');

            $http.post(url, formData, {
                transformRequest: angular.identity,
                headers: {'Content-Type': undefined}
            }).success(function (data, status) {
                deferred.resolve(data.data.batch_id);
            }).error(function (data, status) {
                var result = {};
                if (status == '413') {
                    data = {
                        'data': {
                            'status': 2,
                            'errors': {
                                'content_ads': ['File too large (max 1MB).']
                            }
                        },
                        'success': false
                    };
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                } else if (data && data.data && data.data.errors) {
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                }

                deferred.reject(result);
            });

            return deferred.promise;
        };

        this.checkStatus = function (adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload/' + batchId + '/status/';

            $http.get(url).
                success(function (data) {
                    var result = {};

                    if (data && data.data) {
                        result.status = data.data.status;
                        result.count = data.data.count;
                        result.step = data.data.step;
                        result.batchSize = data.data.batch_size;

                        if (data.data.errors) {
                            result.errors = convertValidationErrorsFromApi(data.data.errors);
                        }
                    }
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.cancel = function (adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload/' + batchId + '/cancel/';

            $http.get(url).success(deferred.resolve).error(deferred.reject);

            return deferred.promise;
        };

        function convertValidationErrorsFromApi (errors) {
            var converted = {
                file: errors.content_ads,
                batchName: errors.batch_name,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
            };

            if (errors.details) {
                converted.details = {
                    reportUrl: errors.details && errors.details.report_url,
                    description: errors.details && errors.details.description,
                };
            }

            return converted;
        }
    }

    function UploadPlus () {
        this.getDefaults = function (adGroupId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload_plus/csv/';

            $http.get(url).
                success(function (data) {
                    var result = {};

                    if (data && data.data) {
                        result.status = data.data.status;

                        if (data.data.defaults) {
                            result.defaults = {
                                displayUrl: data.data.defaults.display_url,
                                brandName: data.data.defaults.brand_name,
                                description: data.data.defaults.description,
                                callToAction: data.data.defaults.call_to_action,
                            };
                        }
                    }
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;

        };

        this.uploadCsv = function (adGroupId, data) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload_plus/csv/';

            var formData = new FormData();
            formData.append('content_ads', data.file);
            formData.append('batch_name', data.batchName ? data.batchName : '');
            formData.append('display_url', data.displayUrl ? data.displayUrl : '');
            formData.append('brand_name', data.brandName ? data.brandName : '');
            formData.append('description', data.description ? data.description : '');
            formData.append('call_to_action', data.callToAction ? data.callToAction : '');

            $http.post(url, formData, {
                transformRequest: angular.identity,
                headers: {'Content-Type': undefined},
            }).success(function (data) {
                deferred.resolve({
                    batchId: data.data.batch_id,
                    candidates: data.data.candidates,
                    errors: convertCandidateErrorsFromApi(data.data.errors),
                });
            }).error(function (data, status) {
                var result = {};
                if (status === '413') {
                    data = {
                        'data': {
                            'status': constants.uploadBatchStatus.FAILED,
                            'errors': {
                                'content_ads': ['File too large (max 1MB).'],
                            },
                        },
                        'success': false,
                    };
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                } else if (data && data.data && data.data.errors) {
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                }

                deferred.reject(result);
            });

            return deferred.promise;
        };

        function convertCandidateErrorsFromApi (errors) {
            var result = {};

            angular.forEach(errors, function (candidateErrors, candidateId) {
                var newErrors = angular.copy(candidateErrors);

                if (newErrors.hasOwnProperty('image_url')) {
                    newErrors.imageUrl = newErrors.image_url;
                    delete newErrors.image_url;
                }

                if (newErrors.hasOwnProperty('image_crop')) {
                    newErrors.imageCrop = newErrors.image_crop;
                    delete newErrors.image_crop;
                }

                if (newErrors.hasOwnProperty('display_url')) {
                    newErrors.displayUrl = newErrors.display_url;
                    delete newErrors.display_url;
                }

                if (newErrors.hasOwnProperty('brand_name')) {
                    newErrors.brandName = newErrors.brand_name;
                    delete newErrors.brand_name;
                }

                if (newErrors.hasOwnProperty('call_to_action')) {
                    newErrors.callToAction = newErrors.call_to_action;
                    delete newErrors.call_to_action;
                }

                if (newErrors.hasOwnProperty('tracker_urls')) {
                    newErrors.trackerUrls = newErrors.tracker_urls;
                    delete newErrors.tracker_urls;
                }

                result[candidateId] = newErrors;
            });

            return result;
        }

        this.checkStatus = function (adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload_plus/' + batchId + '/status/';

            $http.get(url).
                success(function (data) {
                    var result = {
                        candidates: convertStatusFromApi(data.data.candidates),
                    };
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload_plus/' + batchId + '/save/';

            $http.post(url).
                success(function (data) {
                    var result = {
                        numErrors: data.data.num_errors,
                        errorReport: data.data.error_report,
                    };
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.cancel = function (adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/upload_plus/' + batchId + '/cancel/';

            $http.post(url).success(deferred.resolve).error(deferred.reject);

            return deferred.promise;
        };

        function convertStatusFromApi (statuses) {
            var result = [];
            angular.forEach(statuses, function (candidateStatus, candidateId) {
                result[candidateId] = {
                    imageStatus: candidateStatus.image_status,
                    urlStatus: candidateStatus.url_status,
                };
            });
            return result;
        }

        function convertValidationErrorsFromApi (errors) {
            var converted = {
                file: errors.content_ads,
                batchName: errors.batch_name,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
            };

            if (errors.details) {
                converted.details = {
                    reportUrl: errors.details && errors.details.report_url,
                    description: errors.details && errors.details.description,
                };
            }

            return converted;
        }
    }

    function AdGroupContentAdState () {
        this.save = function (adGroupId, state, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/state/';

            $http.post(url, {
                state: state,
                content_ad_ids_selected: contentAdIdsSelected,
                content_ad_ids_not_selected: contentAdIdsNotSelected,
                select_all: selectedAll,
                select_batch: selectedBatch
            }).
                success(function (data) {
                    deferred.resolve(data);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupContentAdArchive () {
        function postToApi (url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var deferred = $q.defer();

            $http.post(url, {
                content_ad_ids_selected: contentAdIdsSelected,
                content_ad_ids_not_selected: contentAdIdsNotSelected,
                select_all: selectedAll,
                select_batch: selectedBatch
            }).
                success(function (data) {
                    deferred.resolve(data);
                }).
                error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        this.archive = function (adGroupId, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var url = '/api/ad_groups/' + adGroupId + '/contentads/archive/';

            return postToApi(url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch);
        };

        this.restore = function (adGroupId, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var url = '/api/ad_groups/' + adGroupId + '/contentads/restore/';

            return postToApi(url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch);
        };
    }

    function AvailableSources () {
        this.list = function () {
            var deferred = $q.defer();
            var url = '/api/sources/';
            var config = {
                params: {}
            };

            addShowArchived(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    deferred.resolve(data);
                }).
                error(function (data, status) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function ConversionGoal () {
        function convertFromApi (conversionGoal) {
            var ret = {
                id: conversionGoal.id,
                type: conversionGoal.type,
                name: conversionGoal.name,
                conversionWindow: conversionGoal.conversion_window,
                goalId: conversionGoal.goal_id
            };

            if (conversionGoal.pixel !== undefined) {
                ret.pixel = conversionGoal.pixel;
            }

            return ret;
        }

        function convertValidationErrorsFromApi (errors) {
            var ret = {};

            if (errors.hasOwnProperty('name')) {
                ret.name = errors.name;
            }

            if (errors.hasOwnProperty('type')) {
                ret.type = errors.type;
            }

            if (errors.hasOwnProperty('conversion_window')) {
                ret.conversionWindow = errors.conversion_window;
            }

            if (errors.hasOwnProperty('goal_id')) {
                ret.goalId = errors.goal_id;
            }

            return ret;
        }

        this.list = function (campaignId) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + campaignId + '/conversion_goals/';

            $http.get(url).
                success(function (data, status) {
                    deferred.resolve({
                        rows: data.data.rows.map(convertFromApi),
                        availablePixels: data.data.available_pixels
                    });
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };

        this.post = function (campaignId, conversionGoal) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + campaignId + '/conversion_goals/';
            var config = {
                name: conversionGoal.name,
                type: conversionGoal.type,
                conversion_window: conversionGoal.conversionWindow,
                goal_id: conversionGoal.goalId
            };

            $http.post(url, config).
                success(function (data, status) {
                    deferred.resolve();
                }).
                error(function (data, status) {
                    var errors = null;
                    if (data.data && data.data.errors) {
                        errors = convertValidationErrorsFromApi(data.data.errors);
                    }
                    return deferred.reject(errors);
                });

            return deferred.promise;
        };

        this.delete = function (campaignId, conversionGoalId) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + campaignId + '/conversion_goals/' + conversionGoalId + '/';

            $http.delete(url).
                success(function (data, status) {
                    deferred.resolve();
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };
    }

    function ConversionPixel () {
        function convertFromApi (conversionPixel) {
            return {
                id: conversionPixel.id,
                slug: conversionPixel.slug,
                url: conversionPixel.url,
                status: conversionPixel.status,
                lastVerifiedDt: conversionPixel.last_verified_dt,
                archived: conversionPixel.archived
            };
        }

        this.list = function (accountId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';

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

        this.post = function (accountId, slug) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';
            var config = {
                slug: slug
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

        this.archive = function (conversionPixelId) {
            var deferred = $q.defer();
            var url = '/api/conversion_pixel/' + conversionPixelId + '/';

            var data = {
                archived: true
            };

            $http.put(url, data).
                success(function (data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };

        this.restore = function (conversionPixelId) {
            var deferred = $q.defer();
            var url = '/api/conversion_pixel/' + conversionPixelId + '/';

            var data = {
                archived: false
            };

            $http.put(url, data).
                success(function (data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };
    }

    // Helpers

    function convertGoals (row, convertedRow) {
        for (var goalName in row['goals']) {
            for (var metricName in row['goals'][goalName]) {
                if (metricName == 'conversions') {
                    convertedRow['goal__' + goalName + ': Conversions'] = row['goals'][goalName][metricName];
                } else if (metricName == 'conversion_rate') {
                    convertedRow['goal__' + goalName + ': Conversion Rate'] = row['goals'][goalName][metricName];
                }
            }
        }
    }

    function convertNotifications (notifications) {
        if (!notifications) {
            return;
        }

        Object.keys(notifications).forEach(function (key) {
            var notification = notifications[key];

            notifications[key] = {
                message: notification.message,
                inProgress: notification.in_progress,
                important: notification.important
            };
        });

        return notifications;
    }


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
                    total: obj.total,
                    comment: obj.comment,
                    allocated: obj.allocated,
                    available: obj.available,
                    amount: obj.amount,
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
                    is_signed: obj.isSigned
                };
            },
            errors: function (resp) {
                return {
                    startDate: resp.data.data.errors.start_date,
                    endDate: resp.data.data.errors.end_date,
                    amount: resp.data.data.errors.amount,
                    licenseFee: resp.data.data.errors.license_fee,
                    comment: resp.data.data.errors.comment
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
                    comment: obj.comment
                };
            },
            dataToApi: function (obj) {
                return {
                    credit: obj.credit.id,
                    amount: obj.amount,
                    start_date: moment(obj.startDate).format('YYYY-MM-DD'),
                    end_date: moment(obj.endDate).format('YYYY-MM-DD'),
                    comment: obj.comment
                };
            },
            error: function (resp) {
                if (!resp.data.data.errors) { return null; }
                return {
                    amount: resp.data.data.errors.amount,
                    startDate: resp.data.data.errors.start_date,
                    endDate: resp.data.data.errors.end_date,
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
            errorsFromApi: function (resp) {
                var errors = resp.data.data.errors;
                if (errors.conversion_goal) {
                    errors.conversionGoal = {
                        goalId: errors.conversion_goal.goal_id,
                        name: errors.conversion_goal.name,
                        type: errors.conversion_goal.type,
                    };
                }
                return errors;
            }
        };

        self.post = function (campaignId, goal) {
            var url = '/api/campaigns/' + campaignId + '/goals/validate/';
            return $http.post(url, self.convert.dataToApi(goal));
        };
    }

    return {
        navigation: new Navigation(),
        user: new User(),
        adGroupSettings: new AdGroupSettings(),
        adGroupSettingsState: new AdGroupSettingsState(),
        adGroupHistory: new AdGroupHistory(),
        adGroupSources: new AdGroupSources(),
        sourcesTable: new SourcesTable(),
        adGroupSourcesTable: new AdGroupSourcesTable(),
        adGroupPublishersTable: new AdGroupPublishersTable(),
        adGroupPublishersState: new AdGroupPublishersState(),
        adGroupAdsTable: new AdGroupAdsTable(),
        adGroupSync: new AdGroupSync(),
        adGroupArchive: new AdGroupArchive(),
        adGroupOverview: new AdGroupOverview(),
        campaignAdGroups: new CampaignAdGroups(),
        campaignAdGroupsTable: new CampaignAdGroupsTable(),
        campaignSettings: new CampaignSettings(),
        campaignHistory: new CampaignHistory(),
        campaignSync: new CampaignSync(),
        campaignArchive: new CampaignArchive(),
        campaignOverview: new CampaignOverview(),
        campaignContentInsights: new CampaignContentInsights(),
        accountHistory: new AccountHistory(),
        accountSettings: new AccountSettings(),
        account: new Account(),
        accountAccountsTable: new AccountAccountsTable(),
        accountCampaigns: new AccountCampaigns(),
        accountCampaignsTable: new AccountCampaignsTable(),
        accountOverview: new AccountOverview(),
        scheduledReports: new ScheduledReports(),
        accountSync: new AccountSync(),
        accountArchive: new AccountArchive(),
        checkAccountsSyncProgress: new CheckAccountsSyncProgress(),
        checkCampaignSyncProgress: new CheckCampaignSyncProgress(),
        checkSyncProgress: new CheckSyncProgress(),
        checkPublisherBlacklistSyncProgress: new CheckPublisherBlacklistSyncProgress(),
        userActivation: new UserActivation(),
        dailyStats: new DailyStats(),
        allAccountsOverview: new AllAccountsOverview(),
        accountUsers: new AccountUsers(),
        adGroupSourceSettings: new AdGroupSourceSettings(),
        adGroupSourcesUpdates: new AdGroupSourcesUpdates(),
        exportAllowed: new ExportAllowed(),
        adGroupAdsExportAllowed: new AdGroupAdsExportAllowed(),
        campaignAdGroupsExportAllowed: new CampaignAdGroupsExportAllowed(),
        adGroupAdsUpload: new AdGroupAdsUpload(),
        uploadPlus: new UploadPlus(),
        availableSources: new AvailableSources(),
        conversionPixel: new ConversionPixel(),
        conversionGoal: new ConversionGoal(),
        adGroupContentAdState: new AdGroupContentAdState(),
        adGroupContentAdArchive: new AdGroupContentAdArchive(),
        accountCredit: new AccountCredit(),
        campaignBudget: new CampaignBudget(),
        campaignGoalValidation: new CampaignGoalValidation(),
        // Also, don't forget to add me to DEMO!
    };
}]);
