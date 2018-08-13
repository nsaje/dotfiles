describe('zemCreateAdGroupSourceAction', function() {
    var $ctrl;
    var zemAdGroupSourcesStateService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector, $componentController) {
        zemAdGroupSourcesStateService = $injector.get(
            'zemAdGroupSourcesStateService'
        );
        var bindings = {
            parentEntity: {
                id: -1,
                type: constants.entityType.AD_GROUP,
            },
        };
        $ctrl = $componentController(
            'zemCreateAdGroupSourceAction',
            {},
            bindings
        );
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });

    it('should crate initialize state service on initialization', function() {
        var service = {
            initialize: jasmine.createSpy(),
            getState: jasmine.createSpy(),
        };
        spyOn(zemAdGroupSourcesStateService, 'getInstance').and.callFake(
            function() {
                return service;
            }
        );
        $ctrl.$onInit();

        expect(zemAdGroupSourcesStateService.getInstance).toHaveBeenCalled();
        expect(service.initialize).toHaveBeenCalled();
    });
});
