describe('component: zemColumnSelector', function() {
    var $componentController;
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        var element = angular.element('<div></div>');
        var locals = {$element: element};
        $ctrl = $componentController('zemColumnSelector', locals);
    }));

    it('shows tooltip msg when column is disabled', function() {
        var hoveredColumn = {disabled: true};

        var response = $ctrl.getTooltip(hoveredColumn);
        expect(response).toEqual(
            'Column is available when corresponding breakdown is visible.'
        );
    });

    it('does not show tooltip msg when column is disabled', function() {
        var hoveredColumn = {disabled: false};

        var response = $ctrl.getTooltip(hoveredColumn);
        expect(response).toEqual(null);
    });

    it('returns all categories/columns when onSearch("") is called', function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('');
        expect($ctrl.filteredCategories[0].columns.length).toBe(5);
    });

    it('finds just one search result when onSearch("column5")', function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('column2');
        expect($ctrl.filteredCategories[0].columns.length).toBe(1);
    });

    it('search is case insensitive', function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('ColuMN2');
        expect($ctrl.filteredCategories[0].columns.length).toBe(1);
    });

    it('does not find any columns when search for non existent column', function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('doesNotExist');
        expect($ctrl.filteredCategories.length).toBe(0);
    });

    it("finds multiple subcategory's columns", function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('subCategory');
        expect($ctrl.filteredCategories[0].subcategories.length).toBe(3);
    });

    it("finds exact subcategory's column", function() {
        $ctrl.categories = generatedCategories();
        $ctrl.onSearch('subCategory1');
        expect($ctrl.filteredCategories[0].subcategories.length).toBe(1);
    });

    function generatedCategories() {
        return [
            {name: 'Category name', columns: generateColumns()},
            {
                name: 'another Category name',
                columns: generateColumns2(),
                subcategories: generateSubcategories(),
            },
        ];
    }

    function generateSubcategories() {
        return [
            {name: 'subCategory1', columns: generateSubColumns()},
            {name: 'subCategory2', columns: generateSubColumns()},
            {name: 'subCategory3', columns: generateSubColumns()},
        ];
    }

    function generateSubColumns() {
        return [
            {data: {field: 'pixel_1554_21'}, visible: false},
            {data: {field: 'pixel_1554_22'}, visible: false},
            {data: {field: 'pixel_1554_23'}, visible: false},
            {data: {field: 'pixel_1554_24'}, visible: false},
            {data: {field: 'pixel_1554_25'}, visible: false},
        ];
    }

    function generateColumns() {
        return [
            {
                data: {name: 'column1', field: 'c1'},
                visible: true,
                disabled: true,
            },
            {
                data: {name: 'column2', field: 'c2'},
                visible: true,
                disabled: false,
            },
            {
                data: {name: 'column3', field: 'c3'},
                visible: true,
                disabled: false,
            },
            {
                data: {name: 'column4', field: 'c4'},
                visible: false,
                disabled: false,
            },
            {
                data: {name: 'column5', field: 'c5'},
                visible: false,
                disabled: true,
            },
        ];
    }

    function generateColumns2() {
        return [
            {
                data: {name: 'column6', field: 'c6'},
                visible: true,
                disabled: true,
            },
            {
                data: {name: 'column7', field: 'c7'},
                visible: true,
                disabled: false,
            },
            {
                data: {name: 'column8', field: 'c8'},
                visible: true,
                disabled: false,
            },
            {
                data: {name: 'column9', field: 'c9'},
                visible: false,
                disabled: false,
            },
        ];
    }
});
