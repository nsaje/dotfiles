describe('component: zemLegacyCampaignGoalsSettings', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, $componentController) {
        var bindings = {
            entity: {settings: {}},
            errors: {},
            api: {register: angular.noop},
        };
        $ctrl = $componentController(
            'zemLegacyCampaignGoalsSettings',
            {},
            bindings
        );
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
