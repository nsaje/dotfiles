/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.config(['$provide', function ($provide) {
    ///////////////////////////
    // API SERVICE DECORATOR //
    ///////////////////////////
    $provide.decorator('api', ['$delegate', '$q', '$window', 'demoDefaults', 'zemLocalStorageService', 'zemDemoCacheService', 'zemDemoAdGroupsService', 'zemDemoSourcesService', 'zemDemoContentAdsService', function ($delegate, $q, $window, demoDefaults, zemLocalStorageService, zemDemoCacheService, zemDemoAdGroupsService, zemDemoSourcesService, zemDemoContentAdsService) {
        if (!$window.isDemo) { return $delegate; }
        var demoInUse = false,
            newCampaigns = {}, // new campaigns map, form: { campaignId1: 1, campaignId2: 1, ...}
            lastSourcesArgs = undefined, // stored last arguments for sources list api
            defaults = demoDefaults,
            // //////////////
            // // WRAPPERS //
            // //////////////
            resetIfErrorWrapper = function (wrappedFn) {
                // If someone refreshes the site while
                // using a created domain, client breaks
                // We want to go to home page if this happens
                // so the user won't notice the error
                return function () {
                    return wrappedFn.apply(null, arguments).then(
                        function (data) { return data; },
                        resetDemo
                    );
                };
            },
            defaultGetWrapper = function (cacheIdTemplate, wrappedFn, httpErrorFn, dataFilterFn) {
                if (!dataFilterFn) { dataFilterFn = function (x) { return x; }; }
                if (!httpErrorFn) { httpErrorFn = function () {}; }
                return function demo (id) {
                    var deferred = $q.defer(),
                        promise = null,
                        cacheId = cacheIdTemplate.replace('{id}', id),
                        cachedResponse = zemDemoCacheService.get(cacheId);
                    if (cachedResponse !== undefined) {
                        deferred.resolve(cachedResponse);
                        return deferred.promise;
                    } else {
                        wrappedFn(id).then(function (data) {
                            data = dataFilterFn(data);
                            zemDemoCacheService.set(cacheId, data);
                            deferred.resolve(data);
                        }, httpErrorFn(cacheId, cachedResponse, deferred));
                        return deferred.promise;
                    }
                };
            },
            //////////////////////
            // HELPER FUNCTIONS //
            //////////////////////
            resetDemo = function (data) {
                var loc = $window.location;
                if (demoInUse) { return data; }
                $window.onbeforeunload = null;
                if (loc.origin) {
                    loc.href = loc.origin + '/';
                } else {
                    loc.href = loc.protocol + '//' + loc.host;
                }
                return data;
            },
            tableMerge = function (original, additional) {
                var additionalRows = additional.rows.slice();
                if (!original.rows.length) {
                    original.rows = additional.rows;
                    return original;
                }
                additionalRows.reverse();
                if (original.pagination.currentPage == 1) {
                    angular.forEach(additionalRows, function (r) {
                        original.rows.unshift(r);
                        original.rows.pop();
                    });
                } else if (original.pagination.currentPage == 2 && original.pagination.size < additionalRows.length) {
                    angular.forEach(additionalRows.slice(6, additional.rows.length), function (r) {
                        original.rows.unshift(r);
                        original.rows.pop();
                    });
                }
                return original;
            },
            capitalize = function (text) {
                return text.charAt(0).toUpperCase() + text.slice(1);
            };

        //////////////////
        // DEMO ACTIONS //
        //////////////////
        $window.demoActions = {
            refreshAdGroupSourcesTable: function () {}
        };

        ///////////////////
        // WINDOW EVENTS //
        ///////////////////
        function confirmOnPageExit (e) {
            e = e || $window.event;
            var message = 'If you leave this page, demo will reset to its initial state.';
            if (e) { e.returnValue = message; }
            return message;
        }
        $window.onbeforeunload = confirmOnPageExit;

        zemDemoSourcesService.setApi($delegate.adGroupSourcesTable.get);

        /* CAMPAIGNS */
        $delegate.accountCampaignsTable.get = (function (backup) {
            return function demo () {
                return backup.apply(null, arguments).then(function (data) {
                    data.is_sync_recent = true;
                    angular.forEach(newCampaigns, function (_, campaignId) {
                        var cached = zemDemoCacheService.get('/api/campaigns/' + campaignId + '/settings/');
                        data.rows.push(defaults.campaignsTableRow(cached.settings.name, campaignId));
                    });
                    return data;
                });
            };
        }($delegate.accountCampaignsTable.get));


        /* ADD CAMPAIGN */
        $delegate.accountCampaigns.create = function demo (id) {
            var deferred = $q.defer(),
                settings = defaults.newCampaignSettings(zemDemoCacheService.generateId('campaign')),
                campaign = angular.extend({}, {
                    campaignManagers: defaults.campaignManagers,
                    history: [{
                        changedBy: 'test.account@zemanta.si',
                        changesText: 'Created settings',
                        showOldSettings: false,
                        datetime: (new Date()).toISOString()
                    }], canArchive: false,  canRestore: false,
                    settings: settings
                });
            newCampaigns[settings.id] = 1;
            demoInUse = true;
            zemDemoCacheService.set('/api/campaigns/' + settings.id + '/settings/', campaign);
            deferred.resolve(settings);
            return deferred.promise;
        };

        /* CAMPAIGN SETTINTS */
        $delegate.campaignSettings.get = resetIfErrorWrapper(
            defaultGetWrapper(
                '/api/campaigns/{id}/settings/',
                $delegate.campaignSettings.get,
                function () { return function () {
                    resetDemo();
                }; }
            )
        );
        $delegate.campaignSettings.save = function demo (settings) {
            var deferred = $q.defer(),
                cacheId = '/api/campaigns/' + settings.id + '/settings/';
            deferred.resolve({settings: settings});
            zemDemoCacheService.update(cacheId, 'settings', settings);
            return deferred.promise;
        };

        $delegate.campaignAgency.get = resetIfErrorWrapper(
            defaultGetWrapper(
                '/api/campaigns/{id}/agency/',
                $delegate.campaignAgency.get,
                function () { return function () {
                    resetDemo();
                }; }
            )
        );
        $delegate.campaignAgency.save = function demo (settings) {
            var deferred = $q.defer(),
                cacheId = '/api/campaigns/' + settings.id + '/agency/',
                history = (zemDemoCacheService.get(cacheId) || {}).history,
                response = {
                    settings: settings,
                    history: history,
                    canArchive: false,
                    canRestore: false
                };
            response.history.push({changedBy: 'test.account@zemanta.si', changesText: 'Updated settings', showOldSettings: false, datetime: (new Date()).toISOString()});
            deferred.resolve(response);
            zemDemoCacheService.update(cacheId, 'settings', settings);
            return deferred.promise;
        };

        /* ADD ADGROUP */
        $delegate.campaignAdGroups.create = function demo (id) {
            var deferred = $q.defer(),
                today = new Date(),
                todayMonth = today.getMonth() + 1,
                settings = defaults.newAdGroupSettings(zemDemoCacheService.generateId('adgroup')),
                campaign = angular.extend({}, {
                    actionIsWaiting: false,
                    settings: settings,
                    defaultSettings: {
                        targetDevices: [
                            {value: 'desktop', checked: false},
                            {value: 'mobile', checked: false},
                        ],
                        targetRegions: [],
                    },
                });
            settings.startDate = moment(
                today.getFullYear() + '-' +
                (todayMonth < 10 ? '0' : '') + todayMonth + '-' +
                today.getDate()
            ).toDate();

            zemDemoCacheService.set('/api/ad_groups/' + settings.id + '/settings/', campaign);
            zemDemoAdGroupsService.newAdGroup(id, settings.id);

            $delegate.availableSources.list().then(function (data) {
                zemDemoCacheService.set('/api/ad_groups/' + settings.id + '/sources/', {
                    sources: defaults.newAdGroupSources(data.data.sources),
                    sourcesWaiting: []
                });
                deferred.resolve(settings);
            });

            demoInUse = true;

            return deferred.promise;
        };

        $delegate.sourcesTable.get = (function demo (backup) {
            return function (level, id) {
                var deferred = null;
                if (level == 'campaigns' && newCampaigns[id]) {
                    deferred = $q.defer();
                    deferred.resolve(defaults.emptySourcesTable());
                    return deferred.promise;
                } else if (level == 'ad_groups' && zemDemoAdGroupsService.isNew(id)) {
                    deferred = $q.defer();
                    deferred.resolve(defaults.emptySourcesTable());
                    return deferred.promise;
                }
                return backup.apply(null, arguments).then(function (data) {
                    data.is_sync_recent = true;
                    return data;
                });
            };
        }(resetIfErrorWrapper($delegate.sourcesTable.get)));

        /* AD GORUPS */
        $delegate.campaignAdGroupsTable.get = (function (backup) {
            return function demo (id, startDate, endDate, order) {
                var deferred = $q.defer(),
                    adGroups = null;
                if (newCampaigns[id]) {
                    adGroups = zemDemoAdGroupsService.getForCampaign(id);
                    if (adGroups.length) {
                        deferred.resolve(zemDemoAdGroupsService.applyToAdGroupTable(
                            id,
                            defaults.emptyTable()
                        ));
                    } else {
                        deferred.resolve(defaults.emptyTable());
                    }
                }
                else {
                    backup(id, startDate, endDate, order).then(function (table) {
                        deferred.resolve(zemDemoAdGroupsService.applyToAdGroupTable(id, table));
                    }, resetDemo);
                }
                return deferred.promise;
            };
        }(resetIfErrorWrapper($delegate.campaignAdGroupsTable.get)));

        /* ADGROUP OVERVIEW */
        $delegate.adGroupOverview.get = resetIfErrorWrapper(
            defaultGetWrapper('/api/ad_groups/{id}/overview/', $delegate.adGroupOverview.get)
        );

        /* ADGROUP OVERVIEW */
        $delegate.campaignOverview.get = resetIfErrorWrapper(
            defaultGetWrapper('/api/campaigns/{id}/overview/', $delegate.campaignOverview.get)
        );

        /* ADGROUP SETTINGS */
        $delegate.adGroupSettings.get = resetIfErrorWrapper(
            defaultGetWrapper('/api/ad_groups/{id}/settings/', $delegate.adGroupSettings.get)
        );
        $delegate.adGroupSettings.save = function demo (settings) {
            var deferred = $q.defer(),
                cacheId = '/api/ad_groups/' + settings.id + '/settings/',
                cacheHistoryId = '/api/ad_groups/' + settings.id + '/agency/',
                cacheStateId = '/api/ad_groups/' + settings.id + '/state/',
                oldSettings = zemDemoCacheService.get(cacheHistoryId),
                agency = oldSettings || {
                    actionIsWaiting: false,
                    settings: settings,
                    defaultSettings: {
                        targetDevices: [
                            {value: 'desktop', checked: false},
                            {value: 'mobile', checked: false},
                        ],
                        targetRegions: [],
                    },
                    history: [
                        {changedBy: 'test.account@zemanta.si',
                          changesText: 'Created settings',
                          showOldSettings: false,
                          datetime: (new Date()).toISOString()},
                    ],
                };
            zemDemoCacheService.update(cacheId, 'settings', settings);
            if (oldSettings) {
                agency.history.push({
                    changedBy: 'test.account@zemanta.si',
                    changesText: 'Updated settings',
                    showOldSettings: false,
                    datetime: (new Date()).toISOString()
                });
            }
            zemDemoCacheService.update(cacheHistoryId, 'history', agency.history);
            zemDemoCacheService.update(cacheHistoryId, 'settings', agency.settings);

            zemDemoCacheService.set(cacheStateId, 'settings', agency);

            zemDemoAdGroupsService.update(settings.id, settings);

            deferred.resolve({
                settings: settings,
                actionIsWaiting: false,
                history: agency.history
            });
            return deferred.promise;
        };

        $delegate.adGroupAgency.get = resetIfErrorWrapper(
            defaultGetWrapper('/api/ad_groups/{id}/agency/', $delegate.adGroupAgency.get)
        );

        /* Ad group media sources */
        $delegate.availableSources.list = defaultGetWrapper('/api/sources/',
                                                            $delegate.availableSources.list);


        $delegate.adGroupSourceSettings.save = function demo (adGroupId, sourceId, data) {
            var deferred = $q.defer(),
                mapped = {
                    cpc_cc: 'bid_cpc',
                    state: 'status_setting'
                },
                newData = {};
            angular.forEach(data, function (value, field) {
                if (mapped[field]) {
                    newData[mapped[field]] = value;
                }
                newData[field] = value;
                if (field.match(/_cc$/)) {
                    newData[field.replace(/_cc$/, '')] = value;
                }
                if (field == 'state') {
                    newData.status_setting = value;
                    newData.status = value == 1 ? 'Active' : 'Paused';
                }
            });
            newData.id = sourceId;
            zemDemoSourcesService.add(adGroupId, sourceId, newData);
            deferred.resolve(true);
            return deferred.promise;
        };

        $delegate.adGroupSources.get = resetIfErrorWrapper(
            defaultGetWrapper('/api/ad_groups/{id}/sources/', $delegate.adGroupSources.get)
        );

        $delegate.adGroupSources.add = function demo (adGroupId, sourceId) {
            var deferred = $q.defer(),
                allSources = zemDemoCacheService.get('/api/sources/'), // this is always called before
                newSource = null;
            angular.forEach(allSources.data.sources || [], function (s) {
                if (s.id == sourceId) { newSource = s; }
            });
            if (newSource) {
                zemDemoSourcesService.create(adGroupId, newSource);
                deferred.resolve(true);

                // Refresh media sources
                $delegate.adGroupSourcesTable.get.apply(null, lastSourcesArgs);
            } else {
                deferred.resolve(false);
            }
            return deferred.promise;
        };

        $delegate.adGroupSourcesTable.get = (function (backup) {
            return function demo (id, startDate, endDate, order) {
                lastSourcesArgs = [id, startDate, endDate, order];
                var deferred = $q.defer();
                zemLocalStorageService.set('columns',
                                           defaults.tableColumns.adGroupSources,
                                          'adGroupSources');
                if (zemDemoAdGroupsService.isNew(id)) {
                    deferred.resolve(
                        zemDemoSourcesService.applyToSourcesTable(
                            id,
                            defaults.newAdGroupSourcesTable()
                        )
                    );
                    return deferred.promise;
                }
                backup(id, startDate, endDate, order).then(function (table) {
                    deferred.resolve(zemDemoSourcesService.applyToSourcesTable(id, table));
                });
                return deferred.promise;
            };

        }(resetIfErrorWrapper($delegate.adGroupSourcesTable.get)));

        /* Content ads */

        $delegate.adGroupAdsUpload.getDefaults = function demo () {
            var deferred = $q.defer(),
                now = new Date();
            deferred.resolve({
                status: true,
                defaults: {
                    displayUrl: 'zemanta.com',
                    brandName: 'Zemanta',
                    description: 'Zemanta Content DSP brings science to the top of the funnel marketing',
                    callToAction: 'Read More'
                }
            });
            return deferred.promise;
        };

        $delegate.adGroupAdsUpload.upload = function demo (adGroupId, data) {
            var deferred = $q.defer(),
                convertFromApi = function (row) {
                    row.titleLink = {
                        text: row.title,
                        url: row.url !== '' ? row.url : null
                    };

                    row.urlLink = {
                        text: row.url !== '' ? row.url : 'N/A',
                        url: row.url !== '' ? row.url : null
                    };
                    return row;
                },
                applyModifications = function (ads) {
                    var rows = ads.rows;
                    angular.forEach(rows, function (r) {
                        convertFromApi(r);
                        r.batch_name = data.batchName;
                        r.upload_time = (new Date()).toISOString();
                        r.brand_name = data.brandName;
                        r.display_url = data.displayUrl;
                        r.description = data.description;
                        r.call_to_action = data.callToAction;
                    });
                    ads.last_change = (new Date()).toISOString();
                    return ads;
                },
                contentAdsIds = [];
            for (var i = 0; i < 8; i++) {
                contentAdsIds.push(zemDemoCacheService.generateId('contentad'));
            }
            deferred.resolve('demo');
            zemDemoCacheService.set('/api/ad_groups/' + adGroupId + '/contentads/table/',
                                    applyModifications(defaults.contentAds(contentAdsIds)));
            zemDemoCacheService.set('/api/ad_groups/' + adGroupId + '/contentads/table/updates/',
                      defaults.contentAdsUpdates);
            return deferred.promise;
        };

        $delegate.adGroupAdsUpload.checkStatus = (function (backup) {
            return function demo (adGroupId, batchId) {
                var deferred = null;
                if (batchId == 'demo') {
                    deferred = $q.defer();
                    deferred.resolve({
                        status: constants.uploadBatchStatus.DONE
                    });
                    return deferred.promise;
                } else {
                    return backup(adGroupId, batchId);
                }
            };
        }($delegate.adGroupAdsUpload.checkStatus));

        $delegate.adGroupAdsTable.get = (function (backup) {
            var applyChanges = function (id, data) {
                angular.forEach(data.rows, function (r) {
                    zemDemoSourcesService.getForAd(id, r);
                    zemDemoContentAdsService.apply(id, r.id, r);
                });
                return data;
            };
            return function demo (id, page, size, startDate, endDate, order) {
                var config = {params: {}},
                    deferred = $q.defer(),
                    cacheId = '/api/ad_groups/' + id + '/contentads/table/',
                    cachedResponse = zemDemoCacheService.get(cacheId);
                zemLocalStorageService.set('columns',
                                            defaults.tableColumns.adGroupAds,
                                           'adGroupContentAds');
                if (cachedResponse && !zemDemoAdGroupsService.isNew(id)) {
                    config.params.order = order;
                    zemDemoSourcesService.refresh(id).then(function () {
                        backup(id, page, size, startDate, endDate, order).then(function (data) {
                            var changes = applyChanges(id, cachedResponse);
                            data.is_sync_recent = true;
                            angular.forEach(data.rows, function (r) {
                                zemDemoSourcesService.getForAd(id, r);
                                zemDemoContentAdsService.apply(id, r.id, r);
                            });
                            deferred.resolve(tableMerge(data, changes));
                        });
                    });
                } else if (zemDemoAdGroupsService.isNew(id)) {
                    if (cachedResponse) {
                        zemDemoSourcesService.refresh(id).then(function () {
                            var data = applyChanges(id, cachedResponse);
                            data.is_sync_recent = true;
                            angular.forEach(data.rows, function (r) {
                                zemDemoSourcesService.getForAd(id, r);
                                zemDemoContentAdsService.apply(id, r.id, r);
                            });
                            deferred.resolve(data);
                        });
                    } else {
                        // error : refresh
                        zemDemoSourcesService.refresh(id).then(function () {
                            deferred.resolve(defaults.emptyTable());
                        });
                    }

                } else {
                    backup(id, page, size, startDate, endDate, order).then(function (data) {
                        zemDemoSourcesService.refresh(id).then(function () {
                            data.is_sync_recent = true;
                            angular.forEach(data.rows, function (r) {
                                zemDemoSourcesService.getForAd(id, r);
                                zemDemoContentAdsService.apply(id, r.id, r);
                            });
                            deferred.resolve(data);
                        });
                    });
                }
                return deferred.promise;
            };
        }(resetIfErrorWrapper($delegate.adGroupAdsTable.get)));

        $delegate.adGroupAdsTable.getUpdates = (function (backup) {
            return function demo (id, lastChange) {
                var deferred = null,
                    cacheId = '/api/ad_groups/' + id + '/contentads/table/updates/',
                    cachedResponse = zemDemoCacheService.get(cacheId);
                if (cachedResponse) {
                    deferred = $q.defer();
                    deferred.resolve(cachedResponse);
                    return deferred.promise;
                } else if (zemDemoAdGroupsService.isNew(id)) {
                    deferred = $q.defer();
                    deferred.resolve({});
                    return deferred.promise;
                } else {
                    return backup(id, lastChange);
                }
            };
        }($delegate.adGroupAdsTable.getUpdates));

        $delegate.adGroupContentAdState.save = function (adGroupId, state, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {
            var deferred = $q.defer();
            zemDemoContentAdsService.setBulk(
                adGroupId, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll,
                {status_setting: state}
            );

            deferred.resolve({success: true});
            return deferred.promise;
        };

        /* Graphs */
        $delegate.dailyStats.listContentAdStats = (function (backup) {
            return function demo (id, startDate, endDate, metrics) {
                var deferred = null;
                if (zemDemoAdGroupsService.isNew(id)) {
                    deferred = $q.defer();
                    deferred.resolve(defaults.emptyChart);
                    return deferred.promise;
                }
                return backup(id, startDate, endDate, metrics);
            };
        }($delegate.dailyStats.listContentAdStats));

        $delegate.dailyStats.list = (function (backup) {
            return function demo (level, id) {
                var deferred = null;
                if (level == 'campaigns' && newCampaigns[id]) {
                    deferred = $q.defer();
                    deferred.resolve(defaults.emptyChart);
                    return deferred.promise;
                }
                if (level == 'ad_groups' && zemDemoAdGroupsService.isNew(id)) {
                    deferred = $q.defer();
                    deferred.resolve(defaults.emptyChart);
                    return deferred.promise;
                }
                return backup.apply(null, arguments);
            };
        }($delegate.dailyStats.list));

        return $delegate;

    }]);
}]);
