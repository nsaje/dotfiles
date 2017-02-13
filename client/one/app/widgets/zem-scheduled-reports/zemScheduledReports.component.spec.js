describe('zemScheduledReports', function () {
    var $injector;
    var $componentController;

    beforeEach(module('one'));
    beforeEach(inject(function (_$injector_) {
        $injector = _$injector_;
        $componentController = $injector.get('$componentController');
    }));

    it('should initialize without errors', function () {
        var $ctrl = $componentController('zemScheduledReports');
        $ctrl.$onInit();
        expect($ctrl.state).toEqual({});
    });
});
