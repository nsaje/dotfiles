/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDemoAdGroupsService', ['zemDemoCacheService', function (zemDemoCacheService) {
    var adGroupData = {},
        campaignToAdGroupsMap = {},
        newAdGroups = []; // new ad groups, form: { adGroupId1: 1, adGroupId2: 1, ...}
    return {
        isNew: function (id) {
            return newAdGroups.indexOf(id) !== -1;
        },
        update: function (id, data) {
            adGroupData[id] = data;
        },
        get: function (id) {
            return adGroupData[id];
        },
        newAdGroup: function (campaignId, adGroupId) {
            if (!campaignToAdGroupsMap[campaignId]) {
                campaignToAdGroupsMap[campaignId] = [];
            }
            campaignToAdGroupsMap[campaignId].push(adGroupId);
            newAdGroups.push(adGroupId);
        },
        getForCampaign: function (campaignId) {
            var list = [];
            angular.forEach(campaignToAdGroupsMap[campaignId], function (id) {
                list.push(adGroupData[id]);
            });
            return list;
        },
        applyToAdGroupTable: function (campaignId, table) {
            table.is_sync_recent = true;
            angular.forEach(table.rows, function (r) {
                angular.forEach(adGroupData[r.ad_group] || {}, function (v, k) {
                    r[k] = v;
                });
            });
            angular.forEach(campaignToAdGroupsMap[campaignId] || [], function (id) {
                var cacheId = '/api/ad_groups/' + id + '/settings/',
                    data = zemDemoCacheService.get(cacheId),
                    row = data.settings;
                row.ad_group = id;
                table.rows.push(angular.copy(row));
            });
            return table;
        }
    };
}]);
