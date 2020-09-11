describe('component: zemGridColumnSelector', function() {
    var $componentController;
    var $ctrl, api, zemAuthStore;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        zemAuthStore = $injector.get('zemAuthStore');
        zemAuthStore.setMockedPermissions([
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

    it('calls setVisibleColumns when onAllColumnsToggled method is called', function() {
        spyOn($ctrl.api, 'setVisibleColumns');
        $ctrl.onAllColumnsToggled();
        expect($ctrl.api.setVisibleColumns).toHaveBeenCalled();
    });

    it('calls findColumnInCategories and setVisibleColumns when onColumnToggled method is called', function() {
        spyOn($ctrl.api, 'findColumnInCategories').and.callThrough();
        spyOn($ctrl.api, 'setVisibleColumns');
        $ctrl.onColumnToggled();
        expect($ctrl.api.setVisibleColumns).toHaveBeenCalled();
        expect($ctrl.api.findColumnInCategories).toHaveBeenCalled();
    });
});
