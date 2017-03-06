describe('component: zemAdGroupSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        $ctrl = $componentController('zemAdGroupSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});
