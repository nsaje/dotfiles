function findBreakdown(tabOptions, breakdownCode) {
    return tabOptions.find(function(x) {
        return x.breakdown === breakdownCode;
    });
}

describe('component: zemGridContainerTabsService', function() {
    var service;

    beforeEach(angular.mock.module('one.widgets'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));
    beforeEach(inject(function(zemGridContainerTabsService, zemPermissions) {
        service = zemGridContainerTabsService;
        zemPermissions.setMockedPermissions([
            'zemauth.can_see_publishers_all_levels',
            'zemauth.can_use_placement_targeting',
            'zemauth.can_see_top_level_delivery_breakdowns',
        ]);
    }));

    it('should allow placement breakdown on all entity levels', function() {
        var levels = [
            undefined,
            {type: constants.entityType.ACCOUNT},
            {type: constants.entityType.CAMPAIGN},
            {type: constants.entityType.AD_GROUP},
        ];

        for (var i = 0; i < levels.length; i++) {
            var tabOptions = service.createTabOptions(levels[i]);
            var additionalBreakDownsTab = findBreakdown(
                tabOptions,
                'publisher'
            );

            expect(
                findBreakdown(additionalBreakDownsTab.options, 'placement')
            ).toEqual({
                name: 'Placements',
                breakdown: 'placement',
                permissions: 'zemauth.can_use_placement_targeting',
                isNewFeature: true,
            });
        }
    });
});
