describe('component: zemDeviceTargetingSettings', function() {
    var $ctrl; // eslint-disable-line no-unused-vars

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, $componentController) {
        var bindings = {
            targetDevices: [],
            targetEnvironments: [],
            targetOs: [],
            errors: {},
            onUpdate: angular.noop,
        };
        $ctrl = $componentController(
            'zemDeviceTargetingSettings',
            {},
            bindings
        );
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
