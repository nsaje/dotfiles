describe('ZemNavigationUtils', function() {
    var zemNavigationUtils;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_zemNavigationUtils_) {
        zemNavigationUtils = _zemNavigationUtils_;
    }));

    function createEntityHierarchy() {
        var size = [2, 2, 4];

        var hierarchy = {};
        hierarchy.children = [];
        for (var accountIdx = 0; accountIdx < size[0]; ++accountIdx) {
            var account = createAccount(accountIdx);
            hierarchy.children.push(account);
            for (var campaignIdx = 0; campaignIdx < size[1]; ++campaignIdx) {
                var campaign = createCampaign(accountIdx, campaignIdx);
                campaign.parent = account;
                account.children.push(campaign);
                for (var adGroupIdx = 0; adGroupIdx < size[2]; ++adGroupIdx) {
                    var adGroup = createAdGroup(
                        accountIdx,
                        campaignIdx,
                        adGroupIdx
                    );
                    adGroup.parent = campaign;
                    campaign.children.push(adGroup);
                }
            }
        }
        return hierarchy;
    }

    function createAccount(accountIdx) {
        accountIdx += 1;
        return {
            type: constants.entityType.ACCOUNT,
            id: parseInt('' + accountIdx + '000'),
            name: 'account ' + accountIdx,
            data: {
                agency: 'agency ' + accountIdx,
            },
            children: [],
        };
    }

    function createCampaign(accountIdx, campaignIdx) {
        accountIdx += 1;
        campaignIdx += 1;
        return {
            type: constants.entityType.CAMPAIGN,
            id: parseInt('' + accountIdx + campaignIdx + '000'),
            name: 'campaign ' + campaignIdx,
            data: {},
            children: [],
        };
    }

    function createAdGroup(accountIdx, campaignIdx, adGroupIdx) {
        accountIdx += 1;
        campaignIdx += 1;
        adGroupIdx += 1;
        return {
            type: constants.entityType.AD_GROUP,
            id: parseInt('' + accountIdx + campaignIdx + adGroupIdx + '000'),
            name: 'adgroup ' + adGroupIdx,
            data: {},
        };
    }

    it('should convert entity hierarchy into flat list', function() {
        var hierarchy = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(hierarchy);
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

    it('should filter list by name while keeping parent entities', function() {
        var hierarchy = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(hierarchy);

        zemNavigationUtils
            .filterEntityList(list, 'account')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(2);
            });

        zemNavigationUtils
            .filterEntityList(list, 'campaign')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(6);
            });

        zemNavigationUtils
            .filterEntityList(list, 'campaign 2')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(4);
            });

        zemNavigationUtils
            .filterEntityList(list, 'adgroup')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(22);
            });

        zemNavigationUtils
            .filterEntityList(list, 'adgroup 2')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(10);
                expect(filteredList[0].type).toEqual(
                    constants.entityType.ACCOUNT
                );
                expect(filteredList[1].type).toEqual(
                    constants.entityType.CAMPAIGN
                );
                expect(filteredList[2].type).toEqual(
                    constants.entityType.AD_GROUP
                );
            });
    });

    it('should filter list by id while keeping parent entities', function() {
        var hierarchy = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(hierarchy);

        zemNavigationUtils
            .filterEntityList(list, '2000')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(1);
                expect(filteredList[0].type).toEqual(
                    constants.entityType.ACCOUNT
                );
            });

        zemNavigationUtils
            .filterEntityList(list, '21000')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(2);
                expect(filteredList[1].type).toEqual(
                    constants.entityType.CAMPAIGN
                );
            });

        zemNavigationUtils
            .filterEntityList(list, '213000')
            .then(function(filteredList) {
                expect(filteredList.length).toBe(3);
                expect(filteredList[2].type).toEqual(
                    constants.entityType.AD_GROUP
                );
            });
    });

    it('should filter archived ad groups', function() {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        zemNavigationUtils
            .filterEntityList(list, '', null, false)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(22);
            });

        list[2].data.archived = true;
        zemNavigationUtils
            .filterEntityList(list, '', null, false)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(21);
            });

        zemNavigationUtils
            .filterEntityList(list, 'adgroup 2', null, false)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(10);
            });
    });

    it('should filter by agency', function() {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        zemNavigationUtils
            .filterEntityList(list, 'agency', null, false)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(0);
            });

        zemNavigationUtils
            .filterEntityList(list, 'agency', null, false, true)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(22);
            });

        zemNavigationUtils
            .filterEntityList(list, 'agency 1', null, false, true)
            .then(function(filteredList) {
                expect(filteredList.length).toBe(11);
            });
    });
});
