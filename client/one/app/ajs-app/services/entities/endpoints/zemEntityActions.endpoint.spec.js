describe('zemEntityActionsEndpoint', function() {
    var zemEntityActionsEndpoint;
    var $httpBackend;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityActionsEndpoint = $injector.get('zemEntityActionsEndpoint');

        $httpBackend.whenPUT(/.*/).respond(200, {});
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

        $httpBackend.expect('PUT', '/rest/internal/accounts/1');
        $httpBackend.expect('PUT', '/rest/internal/campaigns/2');
        $httpBackend.expect('PUT', '/rest/internal/adgroups/3');
        $httpBackend.expect('PUT', '/rest/internal/accounts/4');
        $httpBackend.flush();
    });
});
