/*globals angular,oneApp,constants,options,moment*/
"use strict";

oneApp.factory("zemDemoSourcesService", ['$q', '$window', 'demoDefaults', 'zemDemoCacheService', 'zemDemoAdGroupsService', function($q, $window, demoDefaults, zemDemoCacheService, zemDemoAdGroupsService) {
    var adGroupSourcesDelta = {},
        adGroupSourcesTableRows = {},
        apiGetSourcesTable = null,
        toList = function (adGroup) {
            var values = [];
            angular.forEach(adGroupSourcesDelta[adGroup], function (v) {
                if (v) { values.push(v); }
            });
            return values;
        },
        refreshAdSources = function (adGroup, rows) {
            var deferred = $q.defer();
            if (! apiGetSourcesTable) {
                deferred.reject();
                return deferred.promise;
            }
            if (rows !== undefined) {
                deferred.resolve(true);
                adGroupSourcesTableRows[adGroup] = rows;
                return deferred.promise;
            }
            adGroupSourcesTableRows[adGroup] = demoDefaults.newAdGroupSourcesTable().rows;
            apiGetSourcesTable(adGroup).then(function (data) {
                adGroupSourcesTableRows[adGroup] = data.rows;
                deferred.resolve(true);
            }, function () {
                adGroupSourcesTableRows[adGroup] = demoDefaults.newAdGroupSourcesTable().rows;
                deferred.resolve(true);
            });
            return deferred.promise;
        };
    return {
        setApi: function (apiCall) {
            apiGetSourcesTable = apiCall;
        },
        refresh: function (adGroup) {
            var deferred = null;
            if (adGroupSourcesTableRows[adGroup] === undefined) {
                if (zemDemoAdGroupsService.isNew(adGroup)) {
                    adGroupSourcesTableRows[adGroup] = demoDefaults.newAdGroupSourcesTable().rows;
                    deferred = $q.defer();
                    deferred.resolve(false);
                    return deferred.promise;
                }
                return refreshAdSources(adGroup);
            } else {
                deferred = $q.defer();
                deferred.resolve(false);
                return deferred.promise;
            }
        },
        getForAd: function (adGroup, row) {
            if (! adGroupSourcesTableRows[adGroup]) { return false; }
            row.submission_status = [];
            angular.forEach(adGroupSourcesTableRows[adGroup], function (s) {
                row.submission_status.push({
                    status: s.status_setting == 1 ? 2 : 1,
                    name: s.name,
                    text: s.status_setting == 1 ? 'Approved / Enabled' : 'Paused'
                });
            });
            return row;
        },
        get: function (adGroup, sid) {
            if (! adGroupSourcesDelta[adGroup]) { adGroupSourcesDelta[adGroup] = {}; }
            return sid ? adGroupSourcesDelta[adGroup][sid] : adGroupSourcesDelta[adGroup];
        },
        add: function (adGroup, sid, data) {
            if (! adGroupSourcesDelta[adGroup]) { adGroupSourcesDelta[adGroup] = {}; }
            if (! adGroupSourcesDelta[adGroup][sid]) { adGroupSourcesDelta[adGroup][sid] = {}; }
            angular.forEach(data, function (v, k) {
                adGroupSourcesDelta[adGroup][sid][k] = v;
            });
            $window.demoActions.refreshAdGroupSourcesTable();
        },
        create: function (adGroup, source) {
            var cachedData = zemDemoCacheService.get('/api/ad_groups/' + adGroup + '/sources/'),
                allSources = null;
            angular.forEach(demoDefaults.sourcesRow(), function (v, k) {
                if (!source[k]) { source[k] = v; }
            });

            if (! adGroupSourcesDelta[adGroup]) adGroupSourcesDelta[adGroup] = {};
            adGroupSourcesDelta[adGroup][source.id] = source;

            allSources = cachedData.sources;
            cachedData.sources = [];
            angular.forEach(allSources, function (s) {
                if (s.id != source.id) {
                    cachedData.sources.push(s);
                }
            });
            //cachedData.sourcesWaiting.push(source.name);
            zemDemoCacheService.set('/api/ad_groups/' + adGroup + '/sources/', cachedData);

            $window.demoActions.refreshAdGroupSourcesTable();
        },
        remove: function (adGroup, sid) {
            adGroupSourcesDelta[adGroup][sid] = undefined;
        },
        applyToSourcesTable: function (adGroup, table) {
            var mapper = {},
                pops = 0,
                cachedData = zemDemoCacheService.get('/api/ad_groups/' + adGroup + '/sources/');
            table.is_sync_recent = true;
            angular.forEach(table.rows, function (row) {
                mapper[row.id] = row;
            });
            angular.forEach(adGroupSourcesDelta[adGroup] || [], function (v) {
                if (v._demo_new) {
                    table.rows.push(v);
                    pops += 1; // count added items so we can remove them
                } else {
                    angular.forEach(v, function (value, field) {
                        if (field == 'id') { return; }
                        mapper[v.id][field] = value;
                    });
                }
            });
            adGroupSourcesTableRows[adGroup] = table.rows;
            //while (pops-- > 0) { cachedData.sourcesWaiting.pop(); }
            zemDemoCacheService.set('/api/ad_groups/' + adGroup + '/sources/', cachedData);
            return table;
        },
        applyToAdsTable: function (table) {
            table.is_sync_recent = true;
            return table;
        }
    };
}]);
