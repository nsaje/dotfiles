describe('component: zemSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        $ctrl = $componentController('zemSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});

