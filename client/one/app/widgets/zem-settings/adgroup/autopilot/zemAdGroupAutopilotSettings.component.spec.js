describe('component: zemAdGroupAutopilotSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            entity: {settings: {}},
            errors: {},
            api: {register: angular.noop},
        };
        $ctrl = $componentController('zemAdGroupAutopilotSettings', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
