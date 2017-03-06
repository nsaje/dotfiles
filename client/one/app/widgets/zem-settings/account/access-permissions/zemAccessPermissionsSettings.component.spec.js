describe('component: zemAccessPermissionsSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            entity: {
                settings: {
                    id: -1
                }
            }
        };
        $ctrl = $componentController('zemAccessPermissionsSettings', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
