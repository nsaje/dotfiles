describe('component: zemCampaignTargetingSettings', function() {
    var $ctrl; // eslint-disable-line no-unused-vars

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
            'zemCampaignTargetingSettings',
            {},
            bindings
        );
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
