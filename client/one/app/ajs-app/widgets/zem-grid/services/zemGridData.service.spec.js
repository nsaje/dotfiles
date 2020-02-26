describe('zemGridDataService', function() {
    var $timeout;
    var zemGridParser;

    var grid;
    var gridService;
    var dataSource;
    var endpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(
        angular.mock.module(function($provide, zemGridDebugEndpointProvider) {
            $provide.value('zemLocalStorageService', {get: function() {}});
            $provide.value(
                'zemGridEndpointService',
                zemGridDebugEndpointProvider.$get()
            );
            $provide.value('zemGridStorageService', {
                saveColumns: angular.noop,
                loadColumns: angular.noop,
            });
        })
    );

    beforeEach(inject(function($httpBackend) {
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    beforeEach(inject(function(
        $rootScope,
        _$timeout_,
        zemGridObject,
        zemGridPubSub,
        zemGridDataService,
        zemDataSourceService,
        zemGridDebugEndpoint,
        _zemGridParser_
    ) {
        // eslint-disable-line max-len
        $timeout = _$timeout_;
        zemGridParser = _zemGridParser_;

        endpoint = zemGridDebugEndpoint.createEndpoint();
        dataSource = zemDataSourceService.createInstance(endpoint);

        grid = zemGridObject.createGrid();
        grid.meta.scope = $rootScope.$new();
        grid.meta.pubsub = zemGridPubSub.createInstance(grid.meta.scope);

        gridService = zemGridDataService.createInstance(grid, dataSource);
        grid.meta.dataService = gridService;
    }));

    it('should load meta data on initialization', function() {
        spyOn(dataSource, 'loadMetaData').and.callThrough();

        expect(grid.meta.initialized).toBeFalsy();
        grid.meta.dataService.initialize();
        grid.meta.scope.$apply();
        expect(dataSource.loadMetaData).toHaveBeenCalled();
        expect(grid.meta.initialized).toBe(true);
    });

    it(
        'should load meta data (twice)on initialization to update ' +
            'metadata that can be changed after first data retrieval',
        function() {
            spyOn(dataSource, 'loadMetaData').and.callThrough();
            spyOn(dataSource, 'loadData').and.callThrough();

            grid.meta.dataService.initialize();
            grid.meta.scope.$apply();
            $timeout.flush();

            expect(dataSource.loadData).toHaveBeenCalled();
            expect(dataSource.loadMetaData.calls.count()).toBe(2);
        }
    );

    it('should register to datasource events on initialization', function() {
        spyOn(dataSource, 'onStatsUpdated');
        spyOn(dataSource, 'onDataUpdated');
        grid.meta.dataService.initialize();

        expect(dataSource.onStatsUpdated).toHaveBeenCalled();
        expect(dataSource.onDataUpdated).toHaveBeenCalled();
    });

    it('should notify listeners when data is updated', function() {
        spyOn(grid.meta.pubsub, 'notify');
        grid.meta.dataService.initialize();
        grid.meta.scope.$apply();
        $timeout.flush(); // Endpoint delay
        grid.meta.scope.$apply();
        $timeout.flush(); // Grid data load delay

        expect(grid.meta.pubsub.notify.calls.allArgs()).toEqual([
            [grid.meta.pubsub.EVENTS.METADATA_UPDATED], // first meta data request
            [grid.meta.pubsub.EVENTS.DATA_UPDATED], // initialize root (breakdown tree)
            [grid.meta.pubsub.EVENTS.METADATA_UPDATED], // second meta data request
            [grid.meta.pubsub.EVENTS.DATA_UPDATED], // data retrieved from endpoint and delayed
        ]);

        grid.meta.pubsub.notify.calls.reset();
        grid.meta.dataService.loadData();
        expect(grid.meta.pubsub.notify).toHaveBeenCalledWith(
            grid.meta.pubsub.EVENTS.DATA_UPDATED
        );
    });

    it('should parse retrieved data into grid object', function() {
        spyOn(zemGridParser, 'parse').and.callThrough();
        spyOn(zemGridParser, 'parseMetaData').and.callThrough();

        grid.meta.dataService.initialize();
        grid.meta.scope.$apply();
        $timeout.flush(); // Endpoint delay
        grid.meta.scope.$apply();
        $timeout.flush(); // Grid data load delay

        expect(zemGridParser.parse).toHaveBeenCalled();
        expect(zemGridParser.parseMetaData).toHaveBeenCalled();
        expect(grid.meta.data).toBeDefined();
        expect(grid.header.columns.length).toBeGreaterThan(0);
        expect(grid.body.rows.length).toBeGreaterThan(0);
        expect(grid.footer.row).toBeDefined();
    });

    it('should be able to load data by breakdown and size', function() {
        grid.meta.dataService.initialize();
        grid.meta.scope.$apply();
        $timeout.flush(); // Endpoint delay
        grid.meta.scope.$apply();
        $timeout.flush(); // Grid data load delay

        spyOn(dataSource, 'loadData').and.callThrough();
        var rowsCount = grid.body.rows.length;
        var row = grid.body.rows[grid.body.rows.length - 1]; // Breakdown row

        grid.meta.dataService.loadData(row, 5);
        grid.meta.scope.$apply();
        $timeout.flush();

        expect(dataSource.loadData).toHaveBeenCalledWith(row.data, 5);
        expect(grid.body.rows.length).toBeGreaterThan(rowsCount);
    });

    it('should save data through data source and notify updates', function() {
        grid.meta.dataService.initialize();
        grid.meta.scope.$apply();
        $timeout.flush(); // Endpoint delay
        grid.meta.scope.$apply();
        $timeout.flush(); // Grid data load delay

        spyOn(grid.meta.pubsub, 'notify');
        spyOn(dataSource, 'saveData').and.callThrough();

        var row = grid.body.rows[0];
        var column = grid.header.columns[0];
        grid.meta.dataService.saveData('new value', row, column);
        grid.meta.scope.$apply();

        expect(dataSource.saveData).toHaveBeenCalledWith(
            'new value',
            row.data,
            column.data
        );
        expect(grid.meta.pubsub.notify).toHaveBeenCalledWith(
            grid.meta.pubsub.EVENTS.DATA_UPDATED
        );
        expect(grid.meta.pubsub.notify).toHaveBeenCalledWith(
            grid.meta.pubsub.EVENTS.ROW_UPDATED,
            jasmine.any(Object)
        );
        expect(grid.body.rows[0].data.stats[column.field].value).toBe(
            'new value'
        );
    });
});
