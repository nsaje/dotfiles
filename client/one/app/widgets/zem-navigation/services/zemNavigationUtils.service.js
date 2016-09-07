/* globals angular, oneApp, constants */
/* eslint-disable camelcase */
'use strict';

angular.module('one.widgets').service('zemNavigationUtils', [function () {
    this.convertToEntityList = convertToEntityList;
    this.filterEntityList = filterEntityList;

    function convertToEntityList (accounts) {
        var list = [];
        accounts.forEach(function (account) {
            list.push({data: account, type: constants.entityType.ACCOUNT});
            account.campaigns.forEach(function (campaign) {
                list.push({data: campaign, type: constants.entityType.CAMPAIGN});
                campaign.adGroups.forEach(function (adGroup) {
                    list.push({data: adGroup, type: constants.entityType.AD_GROUP});
                });
            });
        });

        return list;
    }

    function filterEntityList (list, query, showArchived) {
        // Filter list using query and filter state (archived, etc.)
        // Keep parents in list (e.g. keep account and campaign if ad group is present in filtered list)

        query = query.toLowerCase();
        var filteredList = list;

        filteredList = filteredList.filter(function (item) {
            return !item.data.archived || showArchived;
        });

        filteredList = filteredList.filter(function (item) {
            if (item.type !== constants.entityType.AD_GROUP) return true;
            return item.data.name.toLowerCase().indexOf(query) >= 0;
        });

        filteredList = filteredList.filter(function (item, idx) {
            if (item.type !== constants.entityType.CAMPAIGN) return true;
            if (filteredList[idx + 1] && filteredList[idx + 1].type === constants.entityType.AD_GROUP) return true;
            return item.data.name.toLowerCase().indexOf(query) >= 0;
        });

        filteredList = filteredList.filter(function (item, idx) {
            if (item.type !== constants.entityType.ACCOUNT) return true;
            if (filteredList[idx + 1] && filteredList[idx + 1].type === constants.entityType.CAMPAIGN) return true;
            return item.data.name.toLowerCase().indexOf(query) >= 0;
        });

        return filteredList;
    }

}]);
