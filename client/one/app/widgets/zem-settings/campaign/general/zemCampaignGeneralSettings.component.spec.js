describe('component: zemCampaignGeneralSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            entity: {settings: {}},
            errors: {},
            api: {register: angular.noop},
        };
        $ctrl = $componentController('zemCampaignGeneralSettings', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
