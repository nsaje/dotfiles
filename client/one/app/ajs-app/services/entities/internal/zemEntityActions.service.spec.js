describe('zemEntityActionsService', function() {
    var zemEntityActionsService,
        zemEntityActionsEndpoint,
        zemEntityBulkActionsEndpoint;
    var $httpBackend;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        zemEntityActionsService = $injector.get('zemEntityActionsService');
        zemEntityActionsEndpoint = $injector.get('zemEntityActionsEndpoint');
        zemEntityBulkActionsEndpoint = $injector.get(
            'zemEntityBulkActionsEndpoint'
        );

        $httpBackend.whenPOST(/.*/).respond(200, {});
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should use zemEntityActions for entity action', function() {
        spyOn(zemEntityActionsEndpoint, 'activate').and.callThrough();
        var service = zemEntityActionsService.createInstance(
            constants.entityType.AD_GROUP
        );
        var promise = service.activate(1);
        $httpBackend.flush();

        expect(zemEntityActionsEndpoint.activate).toHaveBeenCalled();
        expect(promise.$$state.status).toBe(1);
    });

    it('should use zemEntityBulkActions for bulk action', function() {
        spyOn(zemEntityBulkActionsEndpoint, 'activate').and.callThrough();
        var service = zemEntityActionsService.createInstance(
            constants.entityType.CAMPAIGN
        );
        var promise = service.activateEntities(1, {});
        $httpBackend.flush();

        expect(zemEntityBulkActionsEndpoint.activate).toHaveBeenCalled();
        expect(promise.$$state.status).toBe(1);
    });

    it('should notify when entity action is executed ', function() {
        var service = zemEntityActionsService.createInstance(
            constants.entityType.ACCOUNT
        );
        var spyOnActionExecuted = jasmine.createSpy();
        service.onActionExecuted(spyOnActionExecuted);

        service.archive(1);
        $httpBackend.flush();

        expect(spyOnActionExecuted).toHaveBeenCalledWith(jasmine.any(Object), {
            action: constants.entityAction.ARCHIVE,
            actionType: constants.entityActionType.SINGLE,
            entityType: constants.entityType.ACCOUNT,
            entityId: 1,
            data: jasmine.any(Object),
        });
    });

    it('should notify when bulk action is executed ', function() {
        var service = zemEntityActionsService.createInstance(
            constants.entityType.CAMPAIGN
        );
        var spyOnActionExecuted = jasmine.createSpy();
        service.onActionExecuted(spyOnActionExecuted);

        service.archiveEntities(1, {});
        $httpBackend.flush();

        expect(spyOnActionExecuted).toHaveBeenCalledWith(jasmine.any(Object), {
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.CAMPAIGN,
            action: constants.entityAction.ARCHIVE,
            actionType: constants.entityActionType.BULK,
            entityType: constants.entityType.CAMPAIGN,
            entityId: 1,
            selection: {},
            data: jasmine.any(Object),
        });
    });

    it('should provide getter for accessing supported actions', function() {
        var service = zemEntityActionsService.createInstance(
            constants.entityType.AD_GROUP
        );

        var activate = service.getAction(
            constants.entityActionType.SINGLE,
            constants.entityAction.ACTIVATE
        );
        var deactivate = service.getAction(
            constants.entityActionType.SINGLE,
            constants.entityAction.DEACTIVATE
        );
        var archive = service.getAction(
            constants.entityActionType.SINGLE,
            constants.entityAction.ARCHIVE
        );
        var restore = service.getAction(
            constants.entityActionType.SINGLE,
            constants.entityAction.RESTORE
        );

        expect(activate).toBe(service.activate);
        expect(deactivate).toBe(service.deactivate);
        expect(archive).toBe(service.archive);
        expect(restore).toBe(service.restore);
    });

    it('should provide getter for accessing supported bulk actions', function() {
        var service = zemEntityActionsService.createInstance(
            constants.entityType.AD_GROUP
        );

        var activate = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.ACTIVATE
        );
        var deactivate = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.DEACTIVATE
        );
        var archive = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.ARCHIVE
        );
        var restore = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.RESTORE
        );
        var edit = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.EDIT
        );

        var activateSources = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.ACTIVATE,
            constants.breakdown.MEDIA_SOURCE
        );
        var deactivateSources = service.getAction(
            constants.entityActionType.BULK,
            constants.entityAction.DEACTIVATE,
            constants.breakdown.MEDIA_SOURCE
        );

        expect(activate).toBe(service.activateEntities);
        expect(deactivate).toBe(service.deactivateEntities);
        expect(archive).toBe(service.archiveEntities);
        expect(restore).toBe(service.restoreEntities);
        expect(edit).toBe(service.editEntities);

        expect(activateSources).toBe(service.activateSources);
        expect(deactivateSources).toBe(service.deactivateSources);
    });
});
