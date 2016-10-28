describe('component: zemSettingsMediaSources', function () {
    var ctrl; // eslint-disable-line

    beforeEach(module('one'));
    beforeEach(module('one'), function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            account: {settings: {}},
            errors: {},
            api: {register: angular.noop},
        };
        ctrl = $componentController('zemSettingsMediaSources', {}, bindings);
    }));

    it('should initialize without errors', function () {
    });
});
