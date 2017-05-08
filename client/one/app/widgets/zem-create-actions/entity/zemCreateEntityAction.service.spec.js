describe('component: zemCreateEntityAction', function () {
    var $q, $rootScope, $state;
    var zemEntityService, zemUploadService, zemCreateEntityActionService, zemNavigationService;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function ($injector) {
        $state = $injector.get('$state');
        $q = $injector.get('$q');

        zemCreateEntityActionService = $injector.get('zemCreateEntityActionService');
        zemEntityService = $injector.get('zemEntityService');
        zemUploadService = $injector.get('zemUploadService');
        zemNavigationService = $injector.get('zemNavigationService');
    }));

    it('should create Accounts using zemEntityService', function () {
        spyOn(zemEntityService, 'createEntity').and.callThrough();
        zemCreateEntityActionService.createEntity(constants.entityType.ACCOUNT);
        expect(zemEntityService.createEntity).toHaveBeenCalledWith(constants.entityType.ACCOUNT, undefined);
    });

    it('should create Campaigns using zemEntityService', function () {
        spyOn(zemEntityService, 'createEntity').and.callThrough();
        var parent = {id: -1};
        zemCreateEntityActionService.createEntity(constants.entityType.CAMPAIGN, parent);
        expect(zemEntityService.createEntity).toHaveBeenCalledWith(constants.entityType.CAMPAIGN, -1);
    });

    it('should create AdGroups using zemEntityService', function () {
        spyOn(zemEntityService, 'createEntity').and.callThrough();
        var parent = {id: -1};
        zemCreateEntityActionService.createEntity(constants.entityType.AD_GROUP, parent);
        expect(zemEntityService.createEntity).toHaveBeenCalledWith(constants.entityType.AD_GROUP, -1);
    });

    it('should create ContentAds using upload service', function () {
        spyOn(zemEntityService, 'createEntity').and.callThrough();
        spyOn(zemUploadService, 'openUploadModal').and.callThrough();
        var parent = {id: -1};
        zemCreateEntityActionService.createEntity(constants.entityType.CONTENT_AD, parent);
        expect(zemEntityService.createEntity).not.toHaveBeenCalled();
        expect(zemUploadService.openUploadModal).toHaveBeenCalled();
    });

    describe('after successful creation', function () {
        beforeEach(inject(function ($injector) {
            $rootScope = $injector.get('$rootScope');

            var $httpBackend = $injector.get('$httpBackend');
            $httpBackend.whenGET(/^\/api\/.*\/nav\//).respond(200, {data: {}});

            spyOn(zemEntityService, 'createEntity').and.callFake(function () {
                return $q.resolve({id: 1, name: 'New entity'});
            });
        }));

        it('should reload zemNavigationCache', function () {
            spyOn(zemNavigationService, 'addAccountToCache');

            zemCreateEntityActionService.createEntity(constants.entityType.ACCOUNT);
            $rootScope.$apply();
            expect(zemNavigationService.addAccountToCache).toHaveBeenCalled();
        });

        it('should navigate to newly created entity', function () {
            spyOn($state, 'go');
            zemCreateEntityActionService.createEntity(constants.entityType.ACCOUNT);
            $rootScope.$apply();
            expect($state.go).toHaveBeenCalledWith('v2.analytics',
                {settings: 'create', level: 'account', id: 1, breakdown: undefined});
        });
    });
});
