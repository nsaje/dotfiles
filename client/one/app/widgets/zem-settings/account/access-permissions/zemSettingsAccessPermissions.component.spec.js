describe('component: zemSettingsAccessPermissions', function () {
    var ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            account: {
                settings: {
                    id: -1
                }
            }
        };
        ctrl = $componentController('zemSettingsAccessPermissions', {}, bindings);
    }));

    it('should initialize without errors', function () {
        ctrl.$onInit();
    });
});
