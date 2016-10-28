describe('component: zemSettingsPixels', function () {
    var ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        ctrl = $componentController('zemAccountSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        ctrl.$onInit();
    });
});
