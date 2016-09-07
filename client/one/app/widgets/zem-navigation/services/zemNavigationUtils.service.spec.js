/* globals oneApp, constants, angular, describe, beforeEach, inject, module, it, expect, spyOn */
'use strict';

describe('ZemNavigationUtils', function () {
    var zemNavigationUtils;

    beforeEach(module('one'));
    beforeEach(inject(function (_zemNavigationUtils_) {
        zemNavigationUtils = _zemNavigationUtils_;
    }));

    function createEntityHierarchy () {
        var size = [2, 2, 4];

        var accounts = [];
        for (var accountIdx = 0; accountIdx < size[0]; ++accountIdx) {
            var account = {name: 'account ' + accountIdx, campaigns: []};
            accounts.push(account);
            for (var campaignIdx = 0; campaignIdx < size[1]; ++campaignIdx) {
                var campaign = {name: 'campaign ' + campaignIdx, adGroups: []};
                account.campaigns.push(campaign);
                for (var adGroupIdx = 0; adGroupIdx < size[2]; ++adGroupIdx) {
                    var adGroup = {name: 'adgroup ' + adGroupIdx};
                    campaign.adGroups.push(adGroup);
                }
            }
        }
        return accounts;
    }

    it('should convert entity hierarchy into flat list', function () {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);
        expect(list.length).toBe(22);

        expect(list[0].type).toEqual(constants.entityType.ACCOUNT);
        expect(list[1].type).toEqual(constants.entityType.CAMPAIGN);
        expect(list[2].type).toEqual(constants.entityType.AD_GROUP);
        expect(list[6].type).toEqual(constants.entityType.CAMPAIGN);
        expect(list[7].type).toEqual(constants.entityType.AD_GROUP);
        expect(list[11].type).toEqual(constants.entityType.ACCOUNT);
        expect(list[12].type).toEqual(constants.entityType.CAMPAIGN);
        expect(list[13].type).toEqual(constants.entityType.AD_GROUP);
    });

    it('should filter list while keeping parent entities', function () {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        var filteredList = zemNavigationUtils.filterEntityList(list, 'account');
        expect(filteredList.length).toBe(2);

        filteredList = zemNavigationUtils.filterEntityList(list, 'campaign');
        expect(filteredList.length).toBe(6);

        filteredList = zemNavigationUtils.filterEntityList(list, 'campaign 1');
        expect(filteredList.length).toBe(4);

        filteredList = zemNavigationUtils.filterEntityList(list, 'adgroup');
        expect(filteredList.length).toBe(22);

        filteredList = zemNavigationUtils.filterEntityList(list, 'adgroup 1');
        expect(filteredList.length).toBe(10);
        expect(filteredList[0].type).toEqual(constants.entityType.ACCOUNT);
        expect(filteredList[1].type).toEqual(constants.entityType.CAMPAIGN);
        expect(filteredList[2].type).toEqual(constants.entityType.AD_GROUP);
    });

    it('should filter archived ad groups', function () {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        var filteredList = zemNavigationUtils.filterEntityList(list, '', false);
        expect(filteredList.length).toBe(22);

        list[2].data.archived = true;
        filteredList = zemNavigationUtils.filterEntityList(list, '', false);
        expect(filteredList.length).toBe(21);

        filteredList = zemNavigationUtils.filterEntityList(list, 'adgroup 1', false);
        expect(filteredList.length).toBe(10);
    });

});
