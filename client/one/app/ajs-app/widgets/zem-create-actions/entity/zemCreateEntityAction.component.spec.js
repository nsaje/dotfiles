describe('zemCreateEntityActionComponent', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, $componentController) {
        var bindings = {
            parentEntity: {
                id: -1,
                type: constants.entityType.ACCOUNT,
            },
        };
        $ctrl = $componentController('zemCreateEntityAction', {}, bindings);
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
