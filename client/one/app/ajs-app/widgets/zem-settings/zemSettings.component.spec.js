describe('component: zemSettings', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, $componentController) {
        $ctrl = $componentController('zemSettings', {}, {});
    }));

    it('should initialize without errors', function() {
        $ctrl.$onInit();
    });
});
