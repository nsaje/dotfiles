/*globals angular,oneApp,constants,options,moment*/
"use strict";

oneApp.factory("api", ["$http", "$q", "zemFilterService", function($http, $q, zemFilterService) {
    function addFilteredSources(params) {
        if (zemFilterService.getFilteredSources().length > 0) {
            params.filtered_sources = zemFilterService.getFilteredSources().join(',');
        }
    }

    function addShowArchived(params) {
        if (zemFilterService.getShowArchived()) {
            params.show_archived = zemFilterService.getShowArchived();
        }
    }

    function addShowBlacklistedPublisher(params) {
        if (zemFilterService.getBlacklistedPublishers()) {
            params.show_blacklisted_publishers = zemFilterService.getBlacklistedPublishers();
        }
    }

    function NavData() {
        this.list = function () {
            var deferred = $q.defer();
            var url = '/api/nav_data';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource || []);
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
                    deferred.resolve(convertFromApi(resource));
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertFromApi(data) {
            return {
                id: data.id,
                name: data.name,
                email: data.email,
                permissions: data.permissions,
                timezoneOffset: data.timezone_offset,
                showOnboardingGuidance: data.show_onboarding_guidance
            };
        };
    }

    function AdGroupSources() {
        function convertFromApi(data) {
            var sources = [];
            for (var source, i=0; i<data.sources.length; i++) {
                source = data.sources[i];
                sources.push({
                    id: source.id,
                    name: source.name,
                    canTargetExistingRegions: source.can_target_existing_regions
                });
            }

            return {
                sources: sources,
                sourcesWaiting: data.sources_waiting
            };
        };

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

    function SourcesTable() {
        function convertRow(row) {
            var convertedRow = {};

            for(var field in row) {
                if(field.indexOf('goals') == '0') {
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

        function convertFromApi(data) {
            for(var i = 0; i < data.rows.length; i++) {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupSourcesTable() {
        function convertRow(row) {
            var convertedRow = {};

            for(var field in row) {
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

        function convertFromApi(data) {
            for(var i = 0; i < data.rows.length; i++) {
                var row = data.rows[i];
                data.rows[i] = convertRow(row);
            }
            data.totals = convertRow(data.totals);
            data.lastChange = data.last_change;
            data.dataStatus = data.data_status;
            data.conversionGoals = data.conversion_goals;

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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupPublishersTable() {

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
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupPublishersState() {
        this.save = function(id, state, startDate, endDate, publishersSelected, publishersNotSelected, selectedAll) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/publishers/blacklist/';

            $http.post(url, {
                    state: state,
                    start_date: startDate,
                    end_date: endDate,
                    select_all: selectedAll,
                    publishers_selected: publishersSelected,
                    publishers_not_selected: publishersNotSelected
                }).
                success(function(data) {
                   deferred.resolve(data);
                }).error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAdsTable() {
        function convertFromApi(row) {
            row.titleLink = {
                text: row.title,
                url: row.url !== '' ? row.url : null
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

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        data.data.rows = data.data.rows.map(convertFromApi);
                        deferred.resolve(data.data);
                    }
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAdsPlusTable() {
        function convertFromApi(row) {
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
            var url = '/api/ad_groups/' + id + '/contentadsplus/table/';
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.getUpdates = function(adGroupId, lastChange) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentadsplus/table/updates/';

            var config = {
                params: {}
            };

            if (lastChange) {
                config.params.last_change = lastChange;
            }

            addFilteredSources(config.params);

            $http.get(url, config).
                success(function(data) {
                    deferred.resolve(convertUpdatesFromApi(data.data));
                }).error(function(data) {
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

    function AdGroupSync() {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckSyncProgress() {
        this.get = function(id) {
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

    function CheckPublisherBlacklistSyncProgress() {
        this.get = function(id) {
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
                    function(response) {
                        var resource;
                        if (response && response.data && response.data.success) {
                            deferred.resolve(response.data);
                        }
                    },
                    function(response) {
                        deferred.reject(response);
                    });

            return deferred.promise;
        };
    }

    function AccountSync() {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CheckAccountsSyncProgress() {
        this.get = function() {
            var deferred = $q.defer();
            var url = '/api/accounts/check_sync_progress/';
            var config = {
                params: {}
            };

            addFilteredSources(config.params);

            $http.get(url, config).
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
        this.get = function(campaignId, accountId) {
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

    function UserActivation() {
        this.post = function(accountId, userId) {
            var deferred = $q.defer(),
                url = '/api/accounts/' + accountId + '/users/' + userId + '/activate',
                config = {
                    params: {}
                },
                data = {};

            $http.post(url, config).
                success(function(data, status) {
                    deferred.resolve(data.data);
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

        this.listContentAdStats = function (id, startDate, endDate, metrics) {
            var url = '/api/ad_groups/' + id + '/contentads_plus/daily_stats/';
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

        function getData(url, startDate, endDate, metrics, selectedIds, totals, groupSources) {
            var deferred = $q.defer();
            var config = {
                params: {}
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

            $http.get(url, config).
                success(function (response, status) {
                    var chartData, conversionGoals;
                    if (response && response.data && response.data.chart_data) {
                        chartData = response.data.chart_data.map(function (group) {
                            return convertFromApi(group);
                        });
                    }
                    if (response && response.data && response.data.conversion_goals) {
                        conversionGoals = response.data.conversion_goals;
                    }
                    deferred.resolve({
                        chartData: chartData,
                        conversionGoals: conversionGoals
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
                startDate: settings.start_date ? moment(settings.start_date).toDate() : null,
                endDate: settings.end_date ? moment(settings.end_date).toDate() : null,
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
                trackingCode: settings.tracking_code,
                enableGaTracking: settings.enable_ga_tracking,
                enableAdobeTracking: settings.enable_adobe_tracking,
                adobeTrackingParam: settings.adobe_tracking_param
            };
        }

        function convertAdGroupSourcesFromApi(adGroupSources) {
            var sources = [];
            for (var source, i=0; i < adGroupSources.length; i++) {
                source = adGroupSources[i];
                sources.push({
                    id: source.id,
                    sourceState: source.source_state,
                    sourceName: source.source_name
                });
            }

            return sources;
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
                tracking_code: settings.trackingCode,
                enable_ga_tracking: settings.enableGaTracking,
                enable_adobe_tracking: settings.enableAdobeTracking,
                adobe_tracking_param: settings.adobeTrackingParam,
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
                trackingCode: errors.tracking_code,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
                enableGaTracking: errors.enable_ga_tracking,
                enableAdobeTracking: errors.enable_adobe_tracking,
                adobeTrackingParam: errors.adobe_tracking_param,
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
                        actionIsWaiting: data.data.action_is_waiting,
                        adGroupSources: convertAdGroupSourcesFromApi(data.data.ad_group_sources)
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

    function AdGroupArchive() {
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

    function CampaignArchive() {
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

    function AccountArchive() {
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

    function AccountAgency() {
        function convertSettingsFromApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                defaultAccountManager: settings.default_account_manager,
                defaultSalesRepresentative: settings.default_sales_representative,
                serviceFee: settings.service_fee
            };
        }

        function convertSettingsToApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                default_account_manager: settings.defaultAccountManager,
                default_sales_representative: settings.defaultSalesRepresentative,
                service_fee: settings.serviceFee
            };
        }

        function convertValidationErrorFromApi(errors) {
            return {
                id: errors.id,
                name: errors.name,
                defaultAccountManager: errors.default_account_manager,
                defaultSalesRepresentative: errors.default_sales_representative,
                serviceFee: errors.service_fee
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
                        history: convertHistoryFromApi(data.data.history),
                        accountManagers: data.data.account_managers,
                        salesReps: data.data.sales_reps,
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore
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
                        history: convertHistoryFromApi(data.data.history),
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore,
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
                        id: data.data.id,
                        contentAdsTabWithCMS: data.data.content_ads_tab_with_cms
                    });
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };
    }

    function CampaignBudget() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/budget/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve(data.data);
                }).
                error(function(data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (id, data) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/budget/';
            var config = {
                params: {}
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve(data.data);
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountBudget() {
        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + id + '/budget/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve(data.data);
                }).
                error(function(data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AllAccountsBudget() {
        this.get = function () {
            var deferred = $q.defer();
            var url = '/api/accounts/budget/';

            $http.get(url).
                success(function (data, status) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                    }
                    deferred.resolve(data.data);
                }).
                error(function(data, status, headers) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CampaignAgency() {
        function convertSettingsFromApi(settings) {
            return {
                id: settings.id,
                accountManager: settings.account_manager,
                salesRepresentative: settings.sales_representative,
                IABCategory: settings.iab_category
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
                account_manager: settings.accountManager,
                sales_representative: settings.salesRepresentative,
                iab_category: settings.IABCategory
            };
        }

        function convertValidationErrorFromApi(errors) {
            var result = {
                id: errors.id,
                accountManager: errors.account_manager,
                salesRepresentative: errors.sales_representative,
                IABCategory: errors.iab_category
            };

            return result;
        }


        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/campaigns/' + id + '/agency/';

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
                        canRestore: data.data.can_restore,
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
            var url = '/api/campaigns/' + settings.id + '/agency/';
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
                        history: convertHistoryFromApi(data.data.history),
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore
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

    function CampaignSettings() {
        function convertSettingsFromApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                campaignGoal: settings.campaign_goal,
                goalQuantity: settings.goal_quantity
            };
        }

        function convertSettingsToApi(settings) {
            return {
                id: settings.id,
                name: settings.name,
                campaign_goal: settings.campaignGoal,
                goal_quantity: settings.goalQuantity
            };
        }

        function convertValidationErrorFromApi(errors) {
            var result = {
                id: errors.id,
                name: errors.name,
                campaignGoal: errors.campaign_goal,
                goalQuantity: errors.goal_quantity
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
                        settings: convertSettingsFromApi(data.data.settings)
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
                        settings: convertSettingsFromApi(data.data.settings)
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupAgency() {

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

        this.get = function (id) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + id + '/agency/';
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
                        canArchive: data.data.can_archive,
                        canRestore: data.data.can_restore
                    });
                }).
                error(function(data, status, headers, config) {
                    deferred.reject(data);
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

    function AccountAccountsTable() {
        function convertFromApi(row) {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountCampaignsTable() {
        function convertRowsFromApi(data) {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function CampaignAdGroupsTable() {
        function convertRowsFromApi(data) {
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
                error(function(data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AccountUsers() {
        function convertToApi (data) {
            return {
                first_name: data.firstName,
                last_name: data.lastName,
                email: data.email
            };
        }

        function convertValidationErrorFromApi(errors) {
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

    function AdGroupSourceSettings() {
        function convertValidationErrorFromApi(errors) {
            var result = {
                cpc: errors.cpc_cc,
                dailyBudget: errors.daily_budget_cc,
                state: errors.state
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

    function AdGroupSourcesUpdates() {
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

    function CampaignAdGroupsExportAllowed() {
        function convertFromApi(data) {
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

    function AdGroupAdsExportAllowed() {
        function convertFromApi(data) {
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

    function AdGroupAdsPlusExportAllowed() {
        function convertFromApi(data) {
            return {
                allowed: data.allowed,
                maxDays: data.max_days
            };
        }

        this.get = function (adGroupId, startDate, endDate) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentadsplus/export/allowed/';

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

    function ExportPlusAllowed() {
        function convertFromApi(data) {
            return {
                content_ad: data.content_ad,
                ad_group: data.ad_group,
                campaign: data.campaign,
                account: data.account,
                all_accounts: data.all_accounts
            };
        }

        this.get = function (id_, level_, exportSources) {
            var deferred = $q.defer();

            var urlId = ((level_ == constants.level.ALL_ACCOUNTS)?'':id_+'/');
            var urlSources = ((exportSources.valueOf())?'sources/':'');
            var urlFilteredSources = ((exportSources.valueOf())?'?filtered_sources=' + zemFilterService.getFilteredSources().join(','):'');
            var url = '/api/' + level_ + '/' + urlId + urlSources + 'export_plus/allowed/' + urlFilteredSources;

            var config = {
                params: {}
            };

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

    function AdGroupAdsPlusUpload() {
        this.getDefaults = function(adGroupId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads_plus/upload/';

            $http.get(url).
                success(function(data) {
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
                }).error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;

        };

        this.upload = function(adGroupId, data) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads_plus/upload/';

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
            }).success(function(data, status) {
                deferred.resolve(data.data.batch_id);
            }).error(function(data, status) {
                var result = {};
                if (status == '413') {
                    data = {
                        "data": {
                            "status": 2,
                            "errors": {
                                "content_ads": ["File too large."]
                            }
                        },
                        "success": false
                    };
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                } else if (data && data.data && data.data.errors) {
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                }

                deferred.reject(result);
            });

            return deferred.promise;
        };

        this.checkStatus = function(adGroupId, batchId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads_plus/upload/' + batchId + '/status/';

            $http.get(url).
                success(function(data) {
                    var result = {};

                    if (data && data.data) {
                        result.status = data.data.status;
                        result.count = data.data.count;
                        result.step = data.data.step;
                        result.all = data.data.all;

                        if (data.data.errors) {
                            result.errors = convertValidationErrorsFromApi(data.data.errors);
                        }
                    }
                    deferred.resolve(result);
                }).error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        function convertValidationErrorsFromApi(errors) {
            return {
                file: errors.content_ads,
                batchName: errors.batch_name,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action
            };
        }
    }

    function AdGroupContentAdState() {
        this.save = function(adGroupId, state, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/contentads/state/';

            $http.post(url, {
                    state: state,
                    content_ad_ids_selected: contentAdIdsSelected,
                    content_ad_ids_not_selected: contentAdIdsNotSelected,
                    select_all: selectedAll,
                    select_batch: selectedBatch
                }).
                success(function(data) {
                   deferred.resolve(data);
                }).error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };
    }

    function AdGroupContentAdArchive() {
        function postToApi(url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var deferred = $q.defer();

            $http.post(url, {
                content_ad_ids_selected: contentAdIdsSelected,
                content_ad_ids_not_selected: contentAdIdsNotSelected,
                select_all: selectedAll,
                select_batch: selectedBatch
            }).
                success(function(data) {
                    deferred.resolve(data);
                }).
                error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.archive = function(adGroupId, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var url = '/api/ad_groups/' + adGroupId + '/contentads/archive/';

            return postToApi(url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch);
        };

        this.restore = function(adGroupId, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var url = '/api/ad_groups/' + adGroupId + '/contentads/restore/';

            return postToApi(url, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch);
        };
    };

    function AvailableSources() {
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

    function ConversionGoal() {
        function convertFromApi(conversionGoal) {
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

        function convertValidationErrorsFromApi(errors) {
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

        this.list = function(campaignId) {
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

        this.post = function(campaignId, conversionGoal) {
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
                    if(data.data && data.data.errors) {
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

    function ConversionPixel() {
        function convertFromApi(conversionPixel) {
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
                success(function(data, status) {
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
                success(function(data, status) {
                    deferred.resolve(convertFromApi(data.data));
                }).
                error(function (data, status) {
                    deferred.reject();
                });

            return deferred.promise;
        };
    }

    // Helpers

    function convertGoals(row, convertedRow) {
        for(var goalName in row['goals']) {
            for(var metricName in row['goals'][goalName]) {
                if(metricName == 'conversions') {
                    convertedRow['goal__' + goalName + ': Conversions'] = row['goals'][goalName][metricName];
                } else if(metricName == 'conversion_rate') {
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

    return {
        navData: new NavData(),
        user: new User(),
        adGroupState: new AdGroupState(),
        adGroupSettings: new AdGroupSettings(),
        adGroupAgency: new AdGroupAgency(),
        adGroupSources: new AdGroupSources(),
        sourcesTable: new SourcesTable(),
        adGroupSourcesTable: new AdGroupSourcesTable(),
        adGroupPublishersTable: new AdGroupPublishersTable(),
        adGroupPublishersState: new AdGroupPublishersState(),
        adGroupAdsTable: new AdGroupAdsTable(),
        adGroupAdsPlusTable: new AdGroupAdsPlusTable(),
        adGroupSync: new AdGroupSync(),
        adGroupArchive: new AdGroupArchive(),
        campaignAdGroups: new CampaignAdGroups(),
        campaignAdGroupsTable: new CampaignAdGroupsTable(),
        campaignSettings: new CampaignSettings(),
        campaignAgency: new CampaignAgency(),
        campaignBudget: new CampaignBudget(),
        campaignSync: new CampaignSync(),
        campaignArchive: new CampaignArchive(),
        accountAgency: new AccountAgency(),
        account: new Account(),
        accountAccountsTable: new AccountAccountsTable(),
        accountCampaigns: new AccountCampaigns(),
        accountCampaignsTable: new AccountCampaignsTable(),
        accountBudget: new AccountBudget(),
        accountSync: new AccountSync(),
        accountArchive: new AccountArchive(),
        checkAccountsSyncProgress: new CheckAccountsSyncProgress(),
        checkCampaignSyncProgress: new CheckCampaignSyncProgress(),
        checkSyncProgress: new CheckSyncProgress(),
        checkPublisherBlacklistSyncProgress: new CheckPublisherBlacklistSyncProgress(),
        userActivation: new UserActivation(),
        dailyStats: new DailyStats(),
        allAccountsBudget: new AllAccountsBudget(),
        accountUsers: new AccountUsers(),
        adGroupSourceSettings: new AdGroupSourceSettings(),
        adGroupSourcesUpdates: new AdGroupSourcesUpdates(),
        exportPlusAllowed: new ExportPlusAllowed(),
        adGroupAdsExportAllowed: new AdGroupAdsExportAllowed(),
        adGroupAdsPlusExportAllowed: new AdGroupAdsPlusExportAllowed(),
        campaignAdGroupsExportAllowed: new CampaignAdGroupsExportAllowed(),
        adGroupAdsPlusUpload: new AdGroupAdsPlusUpload(),
        availableSources: new AvailableSources(),
        conversionPixel: new ConversionPixel(),
        conversionGoal: new ConversionGoal(),
        adGroupContentAdState: new AdGroupContentAdState(),
        adGroupContentAdArchive: new AdGroupContentAdArchive()
        // Also, don't forget to add me to DEMO!
    };
}]);
