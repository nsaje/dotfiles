describe('zemGridColumnsService', function() {
    var $rootScope;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridColumnsService;
    var zemGridStorageService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.NgZone'));

    beforeEach(
        angular.mock.module(function($provide) {
            $provide.value('zemGridStorageService', {
                saveColumns: angular.noop,
                loadColumns: angular.noop,
            });
            $provide.value('zemGridUIService', {
                resizeGridColumns: angular.noop,
            });
        })
    );

    beforeEach(inject(function(
        _$rootScope_,
        _zemGridObject_,
        _zemGridPubSub_,
        _zemGridColumnsService_,
        _zemGridStorageService_
    ) {
        // eslint-disable-line max-len
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridColumnsService = _zemGridColumnsService_;
        zemGridStorageService = _zemGridStorageService_;
    }));

    function createGrid() {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.options = {};
        grid.meta.data = {level: 'level1'};
        grid.meta.dataService = {
            getBreakdown: function() {
                return ['base_level', 'age'];
            },
        };

        grid.header.columns.push(zemGridObject.createColumn({exceptions: {}}));
        grid.header.columns.push(zemGridObject.createColumn({exceptions: {}}));
        grid.header.columns.push(zemGridObject.createColumn({exceptions: {}}));

        return grid;
    }

    it('should persist changes to storage service', function() {
        spyOn(zemGridStorageService, 'loadColumns');
        spyOn(zemGridStorageService, 'saveColumns');

        var grid = createGrid();
        var pubsub = grid.meta.pubsub;

        var columnsService = zemGridColumnsService.createInstance(grid);
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(zemGridStorageService.loadColumns).toHaveBeenCalled();

        columnsService.setVisibleColumns(grid.header.columns[0], false);
        expect(zemGridStorageService.saveColumns).toHaveBeenCalled();
    });

    it('should allow setting column visibility', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);

        var columns = grid.header.columns;
        columnsService.setVisibleColumns(columns[0], false);
        expect(columns[0].visible).toBe(false);
        expect(columns[1].visible).toBe(true);
        expect(columns[2].visible).toBe(true);
        expect(columnsService.getVisibleColumns().length).toBe(2);

        columnsService.setVisibleColumns(columns, false);
        expect(columns[0].visible).toBe(false);
        expect(columns[1].visible).toBe(false);
        expect(columns[2].visible).toBe(false);
        expect(columnsService.getVisibleColumns().length).toBe(0);

        columnsService.setVisibleColumns(columns, true);
        expect(columnsService.getVisibleColumns().length).toBe(3);
    });

    it('correctly wraps togglable column inside array', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var output = columnsService.getColumnsToToggle({});
        expect(JSON.stringify(output)).toBe(JSON.stringify([{}]));
    });

    it('returns empty array if there are no toggled columns', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var output = columnsService.getColumnsToToggle(undefined);
        expect(output.length).toBe(0);
    });

    it('goes through allColumns (if) branch', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var output = columnsService.getColumnsToToggle({}, []);
        expect(output.length).toBe(1);
    });

    it('selects columns with autoSelect property', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var toggledColumns = generateToggledColumns();
        var allColumns = generateAllColumns();
        var output = columnsService.getColumnsToToggle(
            toggledColumns,
            allColumns
        );
        expect(output.length).toBe(4);
    });

    it("doesn't select columns with autoSelect value that differs to all fields value", function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var toggledColumns = generateToggledColumns();
        var allColumns = generateAllColumns2();
        var output = columnsService.getColumnsToToggle(
            toggledColumns,
            allColumns
        );
        expect(output.length).toBe(3);
    });

    it('returns togglable columns', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var allColumns = generateAllColumns();
        var output = columnsService.getTogglableColumns(allColumns);
        expect(output.length).toBe(2);
    });

    it('should disable columns that cannot be viewed using current breakdown configuration', function() {
        var grid = createGrid();
        spyOn(grid.meta.dataService, 'getBreakdown');

        var pubsub = grid.meta.pubsub;
        zemGridColumnsService.createInstance(grid);

        var columns = grid.header.columns;
        columns[0].data.exceptions.breakdowns = ['breakdown2', 'breakdown3'];
        columns[1].data.exceptions.breakdowns = ['breakdown4'];
        columns[2].data.exceptions.breakdowns = undefined;

        grid.meta.dataService.getBreakdown.and.returnValue([
            {query: 'breakdown1'},
            {query: 'breakdown2'},
            {query: 'breakdown5'},
        ]);

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);

        expect(columns[0].disabled).toBe(false);
        expect(columns[1].disabled).toBe(true);
        expect(columns[2].disabled).toBe(false);

        grid.meta.dataService.getBreakdown.and.returnValue([
            {query: 'breakdown4'},
        ]);

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);

        expect(columns[0].disabled).toBe(true);
        expect(columns[1].disabled).toBe(false);
        expect(columns[2].disabled).toBe(false);
    });

    it('should disable columns based on custom exceptions that overwrites other ones', function() {
        var grid = createGrid();
        spyOn(grid.meta.dataService, 'getBreakdown');

        var pubsub = grid.meta.pubsub;
        zemGridColumnsService.createInstance(grid);

        var columns = grid.header.columns;
        columns[0].data.exceptions.breakdowns = ['breakdown1', 'breakdown2'];
        grid.meta.dataService.getBreakdown.and.returnValue([
            {query: 'breakdown3'},
        ]);

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(columns[0].disabled).toBe(true);

        columns[0].data.exceptions.custom = [
            {
                level: 'level1',
                breakdown: 'breakdown3',
                shown: true,
            },
        ];

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(columns[0].disabled).toBe(false);
    });

    it('should hide disabled columns', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);

        var columns = grid.header.columns;
        columns[0].disabled = true;
        expect(columnsService.getVisibleColumns().length).toBe(2);

        columns[0].disabled = false;
        expect(columnsService.getVisibleColumns().length).toBe(3);

        columns[0].disabled = undefined;
        expect(columnsService.getVisibleColumns().length).toBe(3);
    });

    it('finds column in categories', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var categories = generateCategories();

        var foundField = columnsService.findColumnInCategories(
            categories,
            'field1'
        );
        expect(foundField).toEqual({field: 'field1'});
    });

    it('find column in subcategories', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var categories = generateCategoriesAndSubcategories();

        var foundField = columnsService.findColumnInCategories(
            categories,
            'subField1'
        );
        expect(foundField).toEqual({field: 'subField1'});
    });

    it('does not find column in categories nor in subcategories', function() {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        var categories = generateCategoriesAndSubcategories();

        var foundField = columnsService.findColumnInCategories(
            categories,
            'does not exist'
        );
        expect(foundField).toBe(null);
    });

    function generateCategories() {
        return [
            {
                columns: [
                    {field: 'field1'},
                    {field: 'field2'},
                    {field: 'field3'},
                ],
            },
        ];
    }

    function generateCategoriesAndSubcategories() {
        return [
            {
                subcategories: [
                    {
                        columns: [
                            {field: 'subField1'},
                            {field: 'subField2'},
                            {field: 'subField3'},
                        ],
                        subcategories: [],
                    },
                ],
                columns: [
                    {field: 'field1'},
                    {field: 'field2'},
                    {field: 'field3'},
                ],
            },
        ];
    }

    function generateToggledColumns() {
        return [{field: 'field 1'}, {field: 'field 2'}, {field: 'field 3'}];
    }

    function generateAllColumns() {
        return [
            {
                data: {
                    autoSelect: 'field 3',
                    shown: true,
                    permanent: false,
                },
                disabled: false,
            },
            {
                data: {
                    autoSelect: 'other field',
                    shown: true,
                    permanent: false,
                },
                disabled: false,
            },
            {
                data: {
                    autoSelect: 'another field',
                    shown: false,
                    permanent: true,
                },
                disabled: false,
            },
        ];
    }

    function generateAllColumns2() {
        return [
            {
                data: {
                    autoSelect: 'not found',
                },
            },
        ];
    }
});
