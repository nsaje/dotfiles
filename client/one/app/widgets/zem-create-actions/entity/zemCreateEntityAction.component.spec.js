describe('zemCreateEntityActionComponent', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(module('one'), function ($provide, zemPermissions) {
        zemPermissions.setMockedPermissions(zemPermissions.ALL_PERMISSIONS);
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            parentEntity: {
                id: -1,
                type: constants.entityType.ACCOUNT
            }
        };
        $ctrl = $componentController('zemCreateEntityAction', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
