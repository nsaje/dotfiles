describe('zemEntityService', function () {
    var zemEntityService, zemAccountService, zemCampaignService, zemAdGroupService, zemContentAdService;
    var $httpBackend;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityService = $injector.get('zemEntityService');
        zemAccountService = $injector.get('zemAccountService');
        zemCampaignService = $injector.get('zemCampaignService');
        zemAdGroupService = $injector.get('zemAdGroupService');
        zemContentAdService = $injector.get('zemContentAdService');

        $httpBackend.whenGET(/.*/).respond(200, {});
        $httpBackend.whenPUT(/.*/).respond(200, {data: {settings: {}, defaultSettings: {}}});
        $httpBackend.whenPOST(/.*/).respond(200, {});
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should provide GET CRUD action for entities', function () {
        spyOn(zemAccountService, 'get').and.callThrough();
        spyOn(zemCampaignService, 'get').and.callThrough();
        spyOn(zemAdGroupService, 'get').and.callThrough();

        zemEntityService.getEntity(constants.entityType.ACCOUNT, 1);
        zemEntityService.getEntity(constants.entityType.CAMPAIGN, 2);
        zemEntityService.getEntity(constants.entityType.AD_GROUP, 3);

        expect(zemAccountService.get).toHaveBeenCalledWith(1);
        expect(zemCampaignService.get).toHaveBeenCalledWith(2);
        expect(zemAdGroupService.get).toHaveBeenCalledWith(3);

        $httpBackend.expectGET('/api/accounts/1/settings/');
        $httpBackend.expectGET('/api/campaigns/2/settings/');
        $httpBackend.expectGET('/api/ad_groups/3/settings/');
        $httpBackend.flush();
    });

    it('should provide CREATE CRUD action for entities', function () {
        spyOn(zemAccountService, 'create').and.callThrough();
        spyOn(zemCampaignService, 'create').and.callThrough();
        spyOn(zemAdGroupService, 'create').and.callThrough();

        zemEntityService.createEntity(constants.entityType.ACCOUNT);
        zemEntityService.createEntity(constants.entityType.CAMPAIGN, 2);
        zemEntityService.createEntity(constants.entityType.AD_GROUP, 3);

        expect(zemAccountService.create).toHaveBeenCalledWith(undefined);
        expect(zemCampaignService.create).toHaveBeenCalledWith(2);
        expect(zemAdGroupService.create).toHaveBeenCalledWith(3);

        $httpBackend.expectPUT('/api/accounts/');
        $httpBackend.expectPUT('/api/accounts/2/campaigns/');
        $httpBackend.expectPUT('/api/campaigns/3/ad_groups/');
        $httpBackend.flush();
    });

    it('should provide UPDATE CRUD action for entities', function () {
        spyOn(zemAccountService, 'update').and.callThrough();
        spyOn(zemCampaignService, 'update').and.callThrough();
        spyOn(zemAdGroupService, 'update').and.callThrough();

        var data = {settings: {}};
        zemEntityService.updateEntity(constants.entityType.ACCOUNT, 1, data);
        zemEntityService.updateEntity(constants.entityType.CAMPAIGN, 2, data);
        zemEntityService.updateEntity(constants.entityType.AD_GROUP, 3, data);

        expect(zemAccountService.update).toHaveBeenCalledWith(1, data);
        expect(zemCampaignService.update).toHaveBeenCalledWith(2, data);
        expect(zemAdGroupService.update).toHaveBeenCalledWith(3, data);

        $httpBackend.expectPUT('/api/accounts/1/settings/');
        $httpBackend.expectPUT('/api/campaigns/2/settings/');
        $httpBackend.expectPUT('/api/ad_groups/3/settings/');
        $httpBackend.flush();
    });

    it('should provide helper to access entity services', function () {
        expect(zemEntityService.getEntityService(constants.entityType.ACCOUNT)).toBe(zemAccountService);
        expect(zemEntityService.getEntityService(constants.entityType.CAMPAIGN)).toBe(zemCampaignService);
        expect(zemEntityService.getEntityService(constants.entityType.AD_GROUP)).toBe(zemAdGroupService);
        expect(zemEntityService.getEntityService(constants.entityType.CONTENT_AD)).toBe(zemContentAdService);
    });

    it('should provide helper to execute entity actions', function () {
        zemEntityService.executeAction(constants.entityAction.ARCHIVE, constants.entityType.ACCOUNT, 1);
        zemEntityService.executeAction(constants.entityAction.RESTORE, constants.entityType.CAMPAIGN, 2);
        zemEntityService.executeAction(constants.entityAction.ACTIVATE, constants.entityType.AD_GROUP, 3);

        $httpBackend.expect('POST', '/api/accounts/1/archive/');
        $httpBackend.expect('POST', '/api/campaigns/2/restore/');
        $httpBackend.expect('POST', '/api/ad_groups/3/settings/state/');
        $httpBackend.flush();
    });

    it('should provide helper to entity BULK actions', function () {
        zemEntityService.executeBulkAction(constants.entityAction.ARCHIVE,
            constants.level.ACCOUNTS, constants.breakdown.CAMPAIGN, 1, {});
        zemEntityService.executeBulkAction(constants.entityAction.RESTORE,
            constants.level.CAMPAIGNS, constants.breakdown.AD_GROUP, 2, {});
        zemEntityService.executeBulkAction(constants.entityAction.ACTIVATE,
            constants.level.AD_GROUPS, constants.breakdown.CONTENT_AD, 3, {});

        $httpBackend.expect('POST', '/api/accounts/1/campaigns/archive/');
        $httpBackend.expect('POST', '/api/campaigns/2/ad_groups/restore/');
        $httpBackend.expect('POST', '/api/ad_groups/3/contentads/state/');
        $httpBackend.flush();
    });

    it('should provide helper to execute MEDIA_SOURCE BULK actions', function () {
        zemEntityService.executeBulkAction(constants.entityAction.ACTIVATE,
            constants.level.ACCOUNTS, constants.breakdown.MEDIA_SOURCE, 1, {});
        zemEntityService.executeBulkAction(constants.entityAction.DEACTIVATE,
            constants.level.CAMPAIGNS, constants.breakdown.MEDIA_SOURCE, 2, {});
        zemEntityService.executeBulkAction(constants.entityAction.ACTIVATE,
            constants.level.AD_GROUPS, constants.breakdown.MEDIA_SOURCE, 3, {});

        $httpBackend.expect('POST', '/api/accounts/1/sources/state/');
        $httpBackend.expect('POST', '/api/campaigns/2/sources/state/');
        $httpBackend.expect('POST', '/api/ad_groups/3/sources/state/');
        $httpBackend.flush();
    });
});

