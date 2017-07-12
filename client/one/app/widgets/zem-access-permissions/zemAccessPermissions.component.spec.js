describe('component: zemAccessPermissions', function () {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            entity: {
                settings: {
                    id: -1
                }
            }
        };
        $ctrl = $componentController('zemAccessPermissions', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
