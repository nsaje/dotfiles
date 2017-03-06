describe('component: zemCampaignSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        $ctrl = $componentController('zemAccountSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
