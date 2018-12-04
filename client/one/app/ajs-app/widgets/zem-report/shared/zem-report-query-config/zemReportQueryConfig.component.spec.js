describe('component: zemReportQueryConfig', function() {
    var $componentController;
    var $ctrl, zemPermissions;

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

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        $ctrl = $componentController('zemReportQueryConfig', locals);
    }));

    it('unselects selected columns', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        $ctrl.toggleColumns(columns, false);

        expect($ctrl.selectedColumns.length).toBe(0);
    });

    it('selects all columns', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = [];
        spyOn($ctrl, 'update').and.callFake(function() {});
        $ctrl.toggleColumns(angular.copy(columns), true);

        expect($ctrl.selectedColumns.length).toBe(3);
    });

    it('selects one column', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        var selectedColumn = ['my selected column'];
        $ctrl.toggleColumns(selectedColumn, true);

        expect($ctrl.selectedColumns.length).toBe(4);
    });

    it('unselects one column', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        var selectedColumn = ['my unselected column'];
        $ctrl.toggleColumns(selectedColumn, false);

        expect($ctrl.selectedColumns.length).toBe(3);
    });

    function getSelectedColumns() {
        return ['Agency', 'Managment', 'Costs'];
    }
});
