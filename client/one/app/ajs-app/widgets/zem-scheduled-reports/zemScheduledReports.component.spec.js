describe('zemScheduledReports', function() {
    var $injector;
    var $componentController;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $componentController = $injector.get('$componentController');
    }));

    it('should initialize without errors', function() {
        var $ctrl = $componentController('zemScheduledReports');
        $ctrl.$onInit();
        expect($ctrl.state).toEqual({});
    });
});
