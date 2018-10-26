describe('component: zemGridColumnSelector', function() {
    var $componentController;
    var $ctrl, api, zemPermissions;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        zemPermissions = $injector.get('zemPermissions');
        zemPermissions.setMockedPermissions([
            'zemauth.can_view_breakdown_by_delivery',
            'zemauth.can_see_managers_in_campaigns_table',
        ]);

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE
        );

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridColumnSelector', locals, bindings);
    }));

    it('calls setVisibleColumns when toggleColumns method is called', function() {
        spyOn($ctrl.api, 'setVisibleColumns');
        $ctrl.toggleColumns();
        expect($ctrl.api.setVisibleColumns).toHaveBeenCalled();
    });

    it('calls findColumnInCategories and setVisibleColumns when onSelectColumn method is called', function() {
        spyOn($ctrl.api, 'findColumnInCategories').and.callThrough();
        spyOn($ctrl.api, 'setVisibleColumns');
        $ctrl.onSelectColumn();
        expect($ctrl.api.setVisibleColumns).toHaveBeenCalled();
        expect($ctrl.api.findColumnInCategories).toHaveBeenCalled();
    });
});
