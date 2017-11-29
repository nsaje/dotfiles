describe('component: zemReportColumnSelector', function () {
    var $componentController;
    var $ctrl;
    var api;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(constants.level.ACCOUNTS, constants.breakdown.MEDIA_SOURCE);

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        var bindings = {api: api};
        $ctrl = $componentController('zemReportColumnSelector', locals, bindings);
    }));


    it('every column is set to true when toggleFunction(true) is called', function () {
        $ctrl.$onInit();
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.toggleColumns = angular.noop;

        $ctrl.onToggleColumns(true);

        var isEveryFieldVisible = $ctrl.bareBoneCategories[0].columns.every(function (obj) {
            if (obj.disabled || obj.visible) {
                return true;
            }
            return false;
        });
        expect(isEveryFieldVisible).toBe(true);
    });

    it('every column is set to false when toggleFunction(false) is called', function () {
        $ctrl.$onInit();
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.toggleColumns = angular.noop;

        $ctrl.onToggleColumns(false);

        var isEveryFieldVisible = $ctrl.bareBoneCategories[0].columns.every(function (obj) {
            if (obj.disabled || !obj.visible) {
                return true;
            }
            return false;
        });
        expect(isEveryFieldVisible).toBe(true);
    });

    function generatedCategories () {
        return [{name: 'Catagory name', columns: generateColumns()}];
    }

    function generateColumns () {
        return [
            {name: 'column1', field: 'c1', visible: true, disabled: true},
            {name: 'column2', field: 'c2', visible: true, disabled: false},
            {name: 'column3', field: 'c3', visible: true, disabled: false},
            {name: 'column4', field: 'c4', visible: false, disabled: false},
            {name: 'column5', field: 'c5', visible: false, disabled: true},
        ];
    }
});
