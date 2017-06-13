describe('component: zemTreeSelect', function () {
    var $ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        var bindings = {
            rootNode: {name: 'root', id: 0, childNodes: []},
            onUpdate: null
        };
        var locals = {
            $element: angular.element('<div></div>')
        };
        $ctrl = $componentController('zemTreeSelect', locals, bindings);
    }));

    it('should initialize without errors', function () {
        $ctrl.$onInit();
    });
});

