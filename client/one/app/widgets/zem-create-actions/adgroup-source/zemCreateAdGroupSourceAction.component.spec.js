describe('zemCreateAdGroupSourceAction', function () {
    var $ctrl;
    var zemAdGroupSourcesStateService;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(module('one'), function ($provide, zemPermissions) {
        zemPermissions.setMockedPermissions(zemPermissions.ALL_PERMISSIONS);
    });

    beforeEach(inject(function ($injector, $componentController) {

        zemAdGroupSourcesStateService = $injector.get('zemAdGroupSourcesStateService');
        var bindings = {
            parentEntity: {
                id: -1,
                type: constants.entityType.AD_GROUP
            }
        };
        $ctrl = $componentController('zemCreateAdGroupSourceAction', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });

    it('should crate initialize state service on initialization', function () {
        var service = {initialize: jasmine.createSpy(), getState: jasmine.createSpy()};
        spyOn(zemAdGroupSourcesStateService, 'getInstance').and.callFake(function () { return service; });
        $ctrl.$onInit();

        expect(zemAdGroupSourcesStateService.getInstance).toHaveBeenCalled();
        expect(service.initialize).toHaveBeenCalled();
    });
});
