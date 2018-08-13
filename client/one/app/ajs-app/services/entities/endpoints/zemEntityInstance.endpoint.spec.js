describe('zemEntityInstanceEndpoint', function() {
    var zemEntityInstanceEndpoint, zemEntityConverter;
    var $httpBackend;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityInstanceEndpoint = $injector.get('zemEntityInstanceEndpoint');
        zemEntityConverter = $injector.get('zemEntityConverter');

        $httpBackend.whenGET(/.*/).respond(200, {data: {settings: {}}});
        $httpBackend
            .whenPUT(/.*/)
            .respond(200, {data: {settings: {}, defaultSettings: {}}});
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should call correct CREATE URLs', function() {
        zemEntityInstanceEndpoint.create(constants.entityType.ACCOUNT, 1);
        zemEntityInstanceEndpoint.create(constants.entityType.CAMPAIGN, 1);
        zemEntityInstanceEndpoint.create(constants.entityType.AD_GROUP, 1);

        $httpBackend.expect('PUT', '/api/accounts/');
        $httpBackend.expect('PUT', '/api/accounts/1/campaigns/');
        $httpBackend.expect('PUT', '/api/campaigns/1/ad_groups/');
        $httpBackend.flush();
    });

    it('should call correct GET URLs', function() {
        zemEntityInstanceEndpoint.get(constants.entityType.ACCOUNT, 1);
        zemEntityInstanceEndpoint.get(constants.entityType.CAMPAIGN, 1);
        zemEntityInstanceEndpoint.get(constants.entityType.AD_GROUP, 1);

        $httpBackend.expect('GET', '/api/accounts/1/settings/');
        $httpBackend.expect('GET', '/api/campaigns/1/settings/');
        $httpBackend.expect('GET', '/api/ad_groups/1/settings/');
        $httpBackend.flush();
    });

    it('should call correct UPDATE URLs', function() {
        zemEntityInstanceEndpoint.update(constants.entityType.ACCOUNT, 1, {
            settings: {},
        });
        zemEntityInstanceEndpoint.update(constants.entityType.CAMPAIGN, 1, {
            settings: {},
            goals: {},
        });
        zemEntityInstanceEndpoint.update(constants.entityType.AD_GROUP, 1, {
            settings: {},
        });

        $httpBackend.expect('PUT', '/api/accounts/1/settings/');
        $httpBackend.expect('PUT', '/api/campaigns/1/settings/');
        $httpBackend.expect('PUT', '/api/ad_groups/1/settings/');
        $httpBackend.flush();
    });

    it('should convert data on GET', function() {
        spyOn(zemEntityConverter, 'convertSettingsFromApi');
        spyOn(zemEntityConverter, 'convertSettingsToApi');

        zemEntityInstanceEndpoint.get(constants.entityType.ACCOUNT, 1);
        $httpBackend.flush();

        expect(zemEntityConverter.convertSettingsFromApi).toHaveBeenCalled();
        expect(zemEntityConverter.convertSettingsToApi).not.toHaveBeenCalled();
    });

    it('should convert data on UPDATE', function() {
        spyOn(zemEntityConverter, 'convertSettingsFromApi');
        spyOn(zemEntityConverter, 'convertSettingsToApi');

        zemEntityInstanceEndpoint.update(constants.entityType.AD_GROUP, 1, {
            settings: {},
        });
        $httpBackend.flush();

        expect(zemEntityConverter.convertSettingsFromApi).toHaveBeenCalled();
        expect(zemEntityConverter.convertSettingsToApi).toHaveBeenCalled();
    });
});
