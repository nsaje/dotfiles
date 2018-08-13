describe('ZemNavigationUtils', function() {
    var zemNavigationUtils;

    beforeEach(angular.mock.module('one'));
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
                var campaign = createCampaign(campaignIdx);
                campaign.parent = account;
                account.children.push(campaign);
                for (var adGroupIdx = 0; adGroupIdx < size[2]; ++adGroupIdx) {
                    var adGroup = createAdGroup(adGroupIdx);
                    adGroup.parent = campaign;
                    campaign.children.push(adGroup);
                }
            }
        }
        return hierarchy;
    }

    function createAccount(idx) {
        return {
            type: constants.entityType.ACCOUNT,
            name: 'account ' + idx,
            data: {
                agency: 'agency ' + idx,
            },
            children: [],
        };
    }

    function createCampaign(idx) {
        return {
            type: constants.entityType.CAMPAIGN,
            name: 'campaign ' + idx,
            data: {},
            children: [],
        };
    }

    function createAdGroup(idx) {
        return {
            type: constants.entityType.AD_GROUP,
            name: 'adgroup ' + idx,
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

    it('should filter list while keeping parent entities', function() {
        var hierarchy = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(hierarchy);

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

    it('should filter archived ad groups', function() {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        var filteredList = zemNavigationUtils.filterEntityList(list, '', false);
        expect(filteredList.length).toBe(22);

        list[2].data.archived = true;
        filteredList = zemNavigationUtils.filterEntityList(list, '', false);
        expect(filteredList.length).toBe(21);

        filteredList = zemNavigationUtils.filterEntityList(
            list,
            'adgroup 1',
            false
        );
        expect(filteredList.length).toBe(10);
    });

    it('should filter by agency', function() {
        var accounts = createEntityHierarchy();
        var list = zemNavigationUtils.convertToEntityList(accounts);

        var filteredList = zemNavigationUtils.filterEntityList(
            list,
            'agency',
            false
        );
        expect(filteredList.length).toBe(0);

        filteredList = zemNavigationUtils.filterEntityList(
            list,
            'agency',
            false,
            true
        );
        expect(filteredList.length).toBe(22);

        filteredList = zemNavigationUtils.filterEntityList(
            list,
            'agency 1',
            false,
            true
        );
        expect(filteredList.length).toBe(11);
    });
});
