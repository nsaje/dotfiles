describe('component: zemReportQueryConfig', function () {
    var $componentController;
    var $ctrl, zemPermissions;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');
        zemPermissions = $injector.get('zemPermissions');
        zemPermissions.setMockedPermissions([
            'zemauth.can_view_breakdown_by_delivery',
            'zemauth.can_see_managers_in_campaigns_table'
        ]);

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        $ctrl = $componentController('zemReportQueryConfig', locals);
    }));

    it('correctly handles selected and unselected columns', function () {
        $ctrl.unSelectedCols = getSelectedCols();
        $ctrl.update = function () {};
        spyOn($ctrl, 'update').and.callFake(function () {});

        var data = {selectedColumns: getSelectedCols(), isChecked: true};
        $ctrl.toggleColumns(data);

        expect($ctrl.unSelectedCols.length).toBe(0);
        expect($ctrl.selectedCols.length).toBe(3);

        data.isChecked = false;
        $ctrl.toggleColumns(data);

        expect($ctrl.selectedCols.length).toBe(0);
        expect($ctrl.unSelectedCols.length).toBe(3);
    });

    it('adds checked column to selected columns', function () {
        $ctrl.unSelectedCols = getSelectedCols();
        $ctrl.selectedCols = getSelectedCols();
        $ctrl.update = function () {};
        spyOn($ctrl, 'update').and.callFake(function () {});

        var column = {name: 'Agency', checked: true};
        $ctrl.selectedColumn(column);
        expect($ctrl.selectedCols.length).toBe(4);
        expect($ctrl.unSelectedCols.length).toBe(2);
    });

    it('removes checked column from uselected columns', function () {
        $ctrl.unSelectedCols = getSelectedCols();
        $ctrl.selectedCols = getSelectedCols();
        $ctrl.update = function () {};
        spyOn($ctrl, 'update').and.callFake(function () {});

        var column = {name: 'Agency', checked: true};
        $ctrl.selectedColumn(column);
        expect($ctrl.unSelectedCols.length).toBe(2);
        expect($ctrl.selectedCols.length).toBe(4);
    });

    function getSelectedCols () {
        return ['Agency', 'Managment', 'Costs'];
    }
});

