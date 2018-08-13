describe('zemEntityBulkActionsEndpoint', function() {
    var zemEntityBulkActionsEndpoint;
    var $httpBackend;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityBulkActionsEndpoint = $injector.get(
            'zemEntityBulkActionsEndpoint'
        );

        $httpBackend.whenPOST(/.*/).respond(200, {});
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should call correct Entity ACTION URLs', function() {
        zemEntityBulkActionsEndpoint.activate(
            constants.level.ALL_ACCOUNTS,
            constants.breakdown.ACCOUNT,
            undefined,
            {}
        );
        zemEntityBulkActionsEndpoint.deactivate(
            constants.level.ACCOUNTS,
            constants.breakdown.CAMPAIGN,
            2,
            {}
        );
        zemEntityBulkActionsEndpoint.archive(
            constants.level.CAMPAIGNS,
            constants.breakdown.AD_GROUP,
            3,
            {}
        );
        zemEntityBulkActionsEndpoint.restore(
            constants.level.AD_GROUPS,
            constants.breakdown.CONTENT_AD,
            4,
            {}
        );
        zemEntityBulkActionsEndpoint.edit(
            constants.level.AD_GROUPS,
            constants.breakdown.CONTENT_AD,
            5,
            {}
        );

        $httpBackend.expect('POST', '/api/all_accounts/accounts/state/');
        $httpBackend.expect('POST', '/api/accounts/2/campaigns/state/');
        $httpBackend.expect('POST', '/api/campaigns/3/ad_groups/archive/');
        $httpBackend.expect('POST', '/api/ad_groups/4/contentads/restore/');
        $httpBackend.expect('POST', '/api/ad_groups/5/contentads/edit/');
        $httpBackend.flush();
    });

    it('should call correct Source ACTION URLs', function() {
        zemEntityBulkActionsEndpoint.activate(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE,
            1,
            {}
        );
        zemEntityBulkActionsEndpoint.deactivate(
            constants.level.CAMPAIGNS,
            constants.breakdown.MEDIA_SOURCE,
            2,
            {}
        );
        zemEntityBulkActionsEndpoint.activate(
            constants.level.AD_GROUPS,
            constants.breakdown.MEDIA_SOURCE,
            3,
            {}
        );

        $httpBackend.expectPOST('/api/accounts/1/sources/state/', {
            state: constants.settingsState.ACTIVE,
        });
        $httpBackend.expectPOST('/api/campaigns/2/sources/state/');
        $httpBackend.expectPOST('/api/ad_groups/3/sources/state/');
        $httpBackend.flush();
    });

    it('should post correct selection data', function() {
        var selection = {
            selectedIds: [1, 2, 3],
            unselectedIds: [4, 5],
            filterAll: true,
            filterId: 3,
        };
        zemEntityBulkActionsEndpoint.archive(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE,
            1,
            selection
        );

        $httpBackend.expectPOST('/api/accounts/1/sources/archive/', {
            selected_ids: [1, 2, 3],
            not_selected_ids: [4, 5],
            select_all: true,
            select_batch: 3,
        });
        $httpBackend.flush();
    });

    it('should post correct state data', function() {
        var selection = {};
        zemEntityBulkActionsEndpoint.activate(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE,
            1,
            selection
        );
        zemEntityBulkActionsEndpoint.deactivate(
            constants.level.CAMPAIGNS,
            constants.breakdown.AD_GROUP,
            1,
            selection
        );

        $httpBackend.expectPOST('/api/accounts/1/sources/state/', {
            state: constants.settingsState.ACTIVE,
        });
        $httpBackend.expectPOST('/api/campaigns/1/ad_groups/state/', {
            state: constants.settingsState.INACTIVE,
        });
        $httpBackend.flush();
    });
});
