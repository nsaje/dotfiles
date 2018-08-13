describe('component: zemAdGroupSettings', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, $componentController) {
        $ctrl = $componentController('zemAdGroupSettings', {}, {});
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
