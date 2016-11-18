describe('component: zemSidePanel', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one'), function () {
    });

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            api: {},
        };
        $ctrl = $componentController('zemSidePanel', {}, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});

