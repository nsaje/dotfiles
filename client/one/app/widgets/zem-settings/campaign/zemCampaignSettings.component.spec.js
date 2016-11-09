describe('component: zemCampaignSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        $ctrl = $componentController('zemCampaignSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
