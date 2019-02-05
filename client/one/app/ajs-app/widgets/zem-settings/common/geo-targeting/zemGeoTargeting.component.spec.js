describe('component: zemGeoTargeting', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($componentController) {
        var bindings = {
            includedLocations: {},
            excludedLocations: {},
            errors: {},
            onUpdate: function() {},
        };
        $ctrl = $componentController('zemGeoTargeting', {}, bindings);
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
