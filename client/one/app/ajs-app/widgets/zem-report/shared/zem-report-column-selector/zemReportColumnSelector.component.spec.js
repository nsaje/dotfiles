describe('component: zemReportColumnSelector', function() {
    var $componentController;
    var $ctrl;
    var api;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE
        );

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        var bindings = {api: api};
        $ctrl = $componentController(
            'zemReportColumnSelector',
            locals,
            bindings
        );
    }));

    it('calls setVisibleColumns when onToggleColumns is called', function() {
        spyOn($ctrl.api, 'getTogglableColumns');
        $ctrl.toggleColumns = angular.noop;
        $ctrl.onToggleColumns();
        expect($ctrl.api.getTogglableColumns).toHaveBeenCalled();
    });

    it('calls api.findColumnInCategories when onSelectColumn is called', function() {
        spyOn($ctrl.api, 'onSelectColumn');
        spyOn($ctrl.api, 'findColumnInCategories');
        $ctrl.toggleColumns = angular.noop;
        $ctrl.onSelectColumn();
        expect($ctrl.api.findColumnInCategories).toHaveBeenCalled();
    });
});
