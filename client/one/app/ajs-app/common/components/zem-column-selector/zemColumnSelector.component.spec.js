describe('component: zemColumnSelector', function () {
    var $componentController;
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');
        var element = angular.element('<div></div>');
        var locals = {$element: element};
        $ctrl = $componentController('zemColumnSelector', locals);
    }));

    it('shows tooltip msg when column is disabled', function () {
        var hoveredColumn = {disabled: true};

        var response = $ctrl.getTooltip(hoveredColumn);
        expect(response).toEqual('Column is available when coresponding breakdown is visible.');
    });

    it('does not show tooltip msg when column is disabled', function () {
        var hoveredColumn = {disabled: false};

        var response = $ctrl.getTooltip(hoveredColumn);
        expect(response).toEqual(null);
    });

    it('returns all categories/columns when onSearch("") is called', function () {
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.$onInit();
        $ctrl.onSearch('');
        expect($ctrl.filteredBareCategories[0].columns.length).toBe(5);
    });

    it('finds just one search result when onSearch("column5")', function () {
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.$onInit();
        $ctrl.onSearch('column5');
        expect($ctrl.filteredBareCategories[0].columns.length).toBe(1);
    });

    it('search is case insensitive', function () {
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.$onInit();
        $ctrl.onSearch('ColuMN5');
        expect($ctrl.filteredBareCategories[0].columns.length).toBe(1);
    });

    it('does not find any columns when search for non exsistant column', function () {
        $ctrl.bareBoneCategories = generatedCategories();
        $ctrl.$onInit();
        $ctrl.onSearch('doesNotExist');
        expect($ctrl.filteredBareCategories.length).toBe(0);
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
