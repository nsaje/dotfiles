describe('zemEntityActionsEndpoint', function() {
    var zemEntityActionsEndpoint;
    var $httpBackend;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityActionsEndpoint = $injector.get('zemEntityActionsEndpoint');

        $httpBackend.whenPOST(/.*/).respond(200, {});
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should call correct ACTION URLs', function() {
        zemEntityActionsEndpoint.activate(constants.entityType.ACCOUNT, 1);
        zemEntityActionsEndpoint.deactivate(constants.entityType.CAMPAIGN, 2);
        zemEntityActionsEndpoint.archive(constants.entityType.AD_GROUP, 3);
        zemEntityActionsEndpoint.restore(constants.entityType.ACCOUNT, 4);

        $httpBackend.expect('POST', '/api/accounts/1/settings/state/');
        $httpBackend.expect('POST', '/api/campaigns/2/settings/state/');
        $httpBackend.expect('POST', '/api/ad_groups/3/archive/');
        $httpBackend.expect('POST', '/api/accounts/4/restore/');
        $httpBackend.flush();
    });
});
