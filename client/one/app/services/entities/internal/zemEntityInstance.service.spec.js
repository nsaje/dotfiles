describe('zemEntityInstance', function () {
    var zemEntityInstanceService, zemEntityInstanceEndpoint;
    var $rootScope, $q, $httpBackend;

    beforeEach(module('one'));
    beforeEach(inject(function ($injector) {
        $q = $injector.get('$q');
        $rootScope = $injector.get('$rootScope');
        $httpBackend = $injector.get('$httpBackend');
        zemEntityInstanceService = $injector.get('zemEntityInstanceService');
        zemEntityInstanceEndpoint = $injector.get('zemEntityInstanceEndpoint');

        zemSpecsHelper.mockUserInitialization($injector);
        $httpBackend.flush();
    }));

    it('should use zemEntityActions endpoint for CRUD operations', function () {
        spyOn(zemEntityInstanceEndpoint, 'create').and.callThrough();
        spyOn(zemEntityInstanceEndpoint, 'get').and.callThrough();
        spyOn(zemEntityInstanceEndpoint, 'update').and.callThrough();

        var service = zemEntityInstanceService.createInstance(constants.entityType.AD_GROUP);
        service.create(1);
        service.get(1);
        service.update(1, {settings: {}});

        expect(zemEntityInstanceEndpoint.create).toHaveBeenCalledWith(constants.entityType.AD_GROUP, 1);
        expect(zemEntityInstanceEndpoint.get).toHaveBeenCalledWith(constants.entityType.AD_GROUP, 1);
        expect(zemEntityInstanceEndpoint.update).toHaveBeenCalledWith(constants.entityType.AD_GROUP, 1, {settings: {}});
    });

    it('should notify when entity is created', function () {
        var spyOnCreated = jasmine.createSpy();
        var service = zemEntityInstanceService.createInstance(constants.entityType.AD_GROUP);
        service.onEntityCreated(spyOnCreated);

        spyOn(zemEntityInstanceEndpoint, 'create').and.callFake(function () {
            return $q.resolve({});
        });

        service.create(1);
        $rootScope.$apply();
        expect(spyOnCreated).toHaveBeenCalledWith(jasmine.any(Object), {
            entityType: constants.entityType.AD_GROUP,
            parentId: 1,
            data: {}
        });
    });

    it('should notify when entity is updated', function () {
        var spyOnUpdated = jasmine.createSpy();
        var service = zemEntityInstanceService.createInstance(constants.entityType.AD_GROUP);
        service.onEntityUpdated(spyOnUpdated);

        spyOn(zemEntityInstanceEndpoint, 'update').and.callFake(function () {
            return $q.resolve({});
        });

        service.update(1, {});
        $rootScope.$apply();
        expect(spyOnUpdated).toHaveBeenCalledWith(jasmine.any(Object), {
            entityType: constants.entityType.AD_GROUP,
            id: 1,
            data: {}
        });
    });
});
