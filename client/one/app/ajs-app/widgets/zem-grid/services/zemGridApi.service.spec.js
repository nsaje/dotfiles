describe('zemGridApi', function() {
    var $rootScope;
    var zemGridApi;
    var zemGridObject;
    var zemGridPubSub;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        _$rootScope_,
        _zemGridObject_,
        _zemGridApi_,
        _zemGridPubSub_
    ) {
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridApi = _zemGridApi_;
        zemGridPubSub = _zemGridPubSub_;
    }));

    function createGrid() {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = generateCategories();
        grid.meta.dataService = {};
        grid.meta.selectionService = {};
        grid.meta.columnsService = {};
        grid.meta.notificationService = {};
        grid.meta.bulkActionsService = {};

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        grid.footer.row = zemGridObject.createRow('', {}, 0, null);

        var baseRow = zemGridObject.createRow('', {}, 1, grid.footer.row);
        grid.body.rows.push(baseRow);
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow));
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow));

        return grid;
    }

    it('should provide high-level interface to grid object', function() {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);

        expect(api.isInitialized()).toBe(grid.meta.initialized);
        expect(api.getMetaData()).toBe(grid.meta.data);
        expect(api.getRows().length).toBe(4); // body rows + footer
        expect(api.getColumns().length).toBe(3);
    });

    it('should register listeners to pubsub', function() {
        var grid = createGrid();
        spyOn(grid.meta.pubsub, 'register');

        var pubsub = grid.meta.pubsub;
        var api = zemGridApi.createInstance(grid);

        expect(grid.meta.pubsub.register).not.toHaveBeenCalled();

        var callback = function() {};
        api.onMetaDataUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.METADATA_UPDATED,
            null,
            callback
        );

        api.onDataUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.DATA_UPDATED,
            null,
            callback
        );

        api.onColumnsUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.EXT_COLUMNS_UPDATED,
            null,
            callback
        );

        api.onSelectionUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.EXT_SELECTION_UPDATED,
            null,
            callback
        );
    });

    it('returns corresponding category', function() {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var zemCostModeService = {
            getCostMode: function() {
                return 'cost mode';
            },
            isTogglableCostMode: function() {
                return false;
            },
        };
        var columns = generateColumns();
        var filteredCategories = api.getCategorizedColumns(
            zemCostModeService,
            columns
        );
        expect(filteredCategories.length).toBe(1);
        expect(filteredCategories[0].name).toBe('category name 1');
    });

    it('returns the right category', function() {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var zemCostModeService = {
            getCostMode: function() {
                return 'cost mode';
            },
            isTogglableCostMode: function() {
                return false;
            },
        };
        var columns = generateColumns2();
        var filteredCategories = api.getCategorizedColumns(
            zemCostModeService,
            columns
        );
        expect(filteredCategories.length).toBe(1);
        expect(filteredCategories[0].name).toBe('category name 2');
    });

    function generateCategories() {
        return {
            categories: [
                {
                    name: 'category name 1',
                    fields: ['field 1', 'field 2', 'field 3'],
                    description: 'category 1 description',
                    type: 'category 1 type',
                    subcategories: [],
                    columns: [],
                },
                {
                    name: 'category name 2',
                    fields: ['field 4'],
                    description: 'category 2 description',
                    type: 'category 2 type',
                    subcategories: [],
                    columns: [],
                },
                {
                    name: 'category name 3',
                    fields: ['field 5', 'field 6'],
                    description: 'category 3 description',
                    type: 'category 3 type',
                    subcategories: [],
                    columns: [],
                },
            ],
        };
    }

    function generateColumns() {
        return [
            {
                field: 'field 1',
                data: {
                    shown: true,
                    permanent: false,
                    costMode: 'cost mode',
                },
            },
            {
                field: 'field 2',
                data: {
                    shown: false,
                    permanent: false,
                    costMode: 'cost mode',
                },
            },
            {
                field: 'field 3',
                data: {
                    shown: true,
                    permanent: true,
                    costMode: 'cost mode',
                },
            },
        ];
    }

    function generateColumns2() {
        return [
            {
                field: 'field 4',
                data: {
                    shown: true,
                    permanent: false,
                    costMode: 'cost mode',
                },
            },
        ];
    }
});
