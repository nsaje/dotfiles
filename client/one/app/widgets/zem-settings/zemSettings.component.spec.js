describe('component: zemSettings', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function () {
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        $ctrl = $componentController('zemSettings', {}, {});
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});

