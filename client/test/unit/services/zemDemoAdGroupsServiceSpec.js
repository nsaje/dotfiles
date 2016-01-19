'use strict';

describe('zemDemoAdGroupsService', function() {
    var cache, adGroups, defaults;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));
    
    beforeEach(inject(function(_zemDemoCacheService_, _zemDemoAdGroupsService_, _demoDefaults_) {
        adGroups = _zemDemoAdGroupsService_;
        defaults = _demoDefaults_;
        cache = _zemDemoCacheService_;
    }));

    it('ad group managament', function () {
        var newAdGroup = { ad_group: 1, name: 'New demo ad group'   },
            existingAdGroup = { ad_group: 2, name: 'Demo ad group' },
            table = defaults.emptyTable();
        adGroups.newAdGroup(1, 1);
        expect(adGroups.isNew(1)).toBe(true);

        expect(JSON.stringify(adGroups.getForCampaign(1))).toBe(JSON.stringify([null]));

        adGroups.update(2, {
            field: 'value'
        });
        expect(adGroups.isNew(2)).toBe(false);

        adGroups.update(1, newAdGroup);
        expect(JSON.stringify(adGroups.getForCampaign(1))).toBe(JSON.stringify([newAdGroup]));

        table.rows.push(existingAdGroup);
        cache.set('/api/ad_groups/1/settings/', {
            settings: newAdGroup
        });
        expect(JSON.stringify(adGroups.applyToAdGroupTable(1, table).rows)).toBe(
            JSON.stringify([
                {ad_group: 2, name: existingAdGroup.name, field: 'value'},
                newAdGroup
            ])
        );
    });
    
});
