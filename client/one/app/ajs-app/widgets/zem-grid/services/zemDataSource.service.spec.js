describe('zemDataSource', function() {
    var $scope;
    var $q;
    var $timeout;
    var dataSource;
    var endpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($httpBackend) {
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    beforeEach(inject(function(
        $rootScope,
        _$q_,
        _$timeout_,
        zemDataSourceService,
        zemGridDebugEndpoint
    ) {
        // eslint-disable-line max-len
        $scope = $rootScope.$new();
        $q = _$q_;
        $timeout = _$timeout_;
        endpoint = zemGridDebugEndpoint.createEndpoint();
        dataSource = zemDataSourceService.createInstance(endpoint);
    }));

    it('should request meta data from endpoint if needed', function() {
        spyOn(endpoint, 'getMetaData').and.callThrough();

        dataSource.loadMetaData();
        $scope.$apply();
        expect(endpoint.getMetaData).toHaveBeenCalled();

        endpoint.getMetaData.calls.reset();
        dataSource.loadMetaData();
        $scope.$apply();
        expect(endpoint.getMetaData).not.toHaveBeenCalled();

        dataSource.loadMetaData(true);
        $scope.$apply();
        expect(endpoint.getMetaData).toHaveBeenCalled();
    });

    it('should request data from endpoint', function() {
        spyOn(endpoint, 'getMetaData').and.callThrough();
        spyOn(endpoint, 'getData').and.callThrough();
        dataSource.loadData();
        $scope.$apply();

        expect(endpoint.getMetaData).toHaveBeenCalled();
        expect(endpoint.getData).toHaveBeenCalled();

        endpoint.getMetaData.calls.reset();
        endpoint.getData.calls.reset();

        dataSource.loadData();
        $scope.$apply();
        expect(endpoint.getMetaData).not.toHaveBeenCalled();
        expect(endpoint.getData).toHaveBeenCalled();
    });

    it('should notify listeners before and after applying data', function() {
        var onLoadListener = jasmine.createSpy();
        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onLoad($scope, onLoadListener);
        dataSource.onDataUpdated($scope, onDataUpdatedListener);

        dataSource.loadData();
        $scope.$apply();
        $timeout.flush();

        expect(onLoadListener).toHaveBeenCalled();
        expect(onDataUpdatedListener).toHaveBeenCalled();
    });

    it('should initialize root when requesting base level data', function() {
        dataSource.loadData();
        $scope.$apply();

        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onDataUpdated($scope, onDataUpdatedListener);
        dataSource.loadData();

        var emptyBreakdownRoot = {
            breakdown: null,
            stats: null,
            level: 0,
            meta: {},
        };
        expect(onDataUpdatedListener).toHaveBeenCalledWith(
            jasmine.any(Object),
            emptyBreakdownRoot
        );
    });

    it('should build breakdown tree through sequential requests', function() {
        // Level 1 (base level) breakdown
        var breakdownL1 = {
            breakdownId: 1,
            level: 1,
            pagination: {
                offset: 0,
                limit: 2,
            },
            rows: [{breakdownId: 11}, {breakdownId: 12}],
            totals: [1, 2, 3],
        };

        // Level 2 breakdowns
        var breakdownL21 = {
            breakdownId: 11,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            rows: [{}],
        };
        var breakdownL22 = {
            breakdownId: 12,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            rows: [{}],
        };

        // Resulting tree
        var breakdownRoot = {
            breakdown: {
                breakdownId: 1,
                level: 1,
                pagination: {
                    offset: 0,
                    limit: 2,
                },
                rows: [
                    {
                        breakdownId: 11,
                        breakdown: {
                            level: 2,
                            breakdownId: 11,
                            pagination: {
                                offset: 0,
                                limit: 1,
                                count: undefined,
                                complete: undefined,
                            },
                            rows: [{}],
                            meta: {loading: false},
                        },
                    },
                    {
                        breakdownId: 12,
                        breakdown: {
                            level: 2,
                            breakdownId: 12,
                            pagination: {
                                offset: 0,
                                limit: 1,
                                count: undefined,
                                complete: undefined,
                            },
                            rows: [{}],
                            meta: {loading: false},
                        },
                    },
                ],
                meta: {},
            },
            level: 0,
            stats: [1, 2, 3],
            meta: {},
        };

        // Mock endpoint responses
        spyOn(endpoint, 'getData').and.returnValues(
            $q.resolve([breakdownL1]),
            $q.resolve([breakdownL21, breakdownL22])
        );

        // Initialize data source with metadata
        dataSource.loadMetaData();
        $scope.$apply();
        dataSource.setBreakdown([{}, {}]);

        // Initialize listeners and request data
        var onLoadListener = jasmine.createSpy();
        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onLoad($scope, onLoadListener);
        dataSource.onDataUpdated($scope, onDataUpdatedListener);
        dataSource.loadData();
        $scope.$apply();

        // Check if everything has been notified with correct structures
        expect(onLoadListener).toHaveBeenCalledWith(
            jasmine.any(Object),
            breakdownL1
        );
        expect(onLoadListener).toHaveBeenCalledWith(
            jasmine.any(Object),
            breakdownL21
        );
        expect(onLoadListener).toHaveBeenCalledWith(
            jasmine.any(Object),
            breakdownL22
        );
        expect(onDataUpdatedListener).toHaveBeenCalledWith(
            jasmine.any(Object),
            breakdownRoot
        );
    });

    it('should be able to request data by breakdown and size', function() {
        spyOn(endpoint, 'getData').and.returnValue($q.resolve([]));
        var breakdown = {
            breakdownId: 11,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            meta: {loading: false},
            rows: [{}],
        };

        dataSource.loadData(breakdown, 10);
        $scope.$apply();

        expect(endpoint.getData).toHaveBeenCalledWith({
            level: 2,
            offset: 1,
            limit: 10,
            breakdownParents: [11],
            breakdown: jasmine.any(Array),
            order: jasmine.any(String),
        });
    });

    it('should save data using endpoint service and correctly apply updated data', function() {
        var baseData = {
            breakdownId: 1,
            level: 1,
            pagination: {
                offset: 0,
                limit: 2,
            },
            rows: [
                {
                    breakdownId: 11,
                    stats: {field1: {value: 11}, field2: {value: 12}},
                },
                {
                    breakdownId: 12,
                    stats: {field1: {value: 21}, field2: {value: 22}},
                },
            ],
            totals: {field1: {value: 1}, field2: {value: 2}},
        };

        var updatedData = {
            rows: [
                {
                    breakdownId: 11,
                    stats: {field1: {value: 110}, field2: {value: 120}},
                },
                {
                    breakdownId: 12,
                    stats: {field1: {value: 210}},
                },
            ],
            totals: {field1: {value: 10}, field2: {value: 20}},
        };

        var updatedStats = [
            {field1: {value: 110}, field2: {value: 120}},
            {field1: {value: 210}, field2: {value: 22}},
            {field1: {value: 10}, field2: {value: 20}},
        ];

        var value = 120;
        var row = baseData.rows[0];
        var column = {field: 'field2'};

        spyOn(endpoint, 'getData').and.returnValue($q.resolve([baseData]));
        spyOn(endpoint, 'saveData').and.returnValue($q.resolve(updatedData));

        dataSource.loadMetaData();
        $scope.$apply();
        dataSource.loadData();
        $scope.$apply();

        var onStatsUpdated = jasmine.createSpy();
        dataSource.onStatsUpdated($scope, onStatsUpdated);

        dataSource.saveData(value, row, column);
        $scope.$apply();

        expect(endpoint.saveData).toHaveBeenCalledWith(
            value,
            row,
            column,
            jasmine.any(Object)
        );
        expect(onStatsUpdated).toHaveBeenCalledWith(
            jasmine.any(Object),
            updatedStats
        );
    });

    it('should apply diff on data', function() {
        var baseData = {
            breakdownId: 1,
            level: 1,
            pagination: {
                offset: 0,
                limit: 2,
            },
            rows: [
                {
                    breakdownId: 11,
                    stats: {field1: {value: 11}, field2: {value: 12}},
                },
                {
                    breakdownId: 12,
                    stats: {field1: {value: 21}, field2: {value: 22}},
                },
            ],
            totals: {field1: {value: 1}, field2: {value: 2}},
        };

        var updatedData = {
            rows: [
                {
                    breakdownId: 11,
                    stats: {field1: {value: 110}, field2: {value: 120}},
                },
                {
                    breakdownId: 12,
                    stats: {field1: {value: 210}},
                },
            ],
            totals: {field1: {value: 10}, field2: {value: 20}},
        };

        var updatedStats = [
            {field1: {value: 110}, field2: {value: 120}},
            {field1: {value: 210}, field2: {value: 22}},
            {field1: {value: 10}, field2: {value: 20}},
        ];

        spyOn(endpoint, 'getData').and.returnValue($q.resolve([baseData]));

        dataSource.loadMetaData();
        $scope.$apply();
        dataSource.loadData();
        $scope.$apply();

        var onStatsUpdated = jasmine.createSpy();
        dataSource.onStatsUpdated($scope, onStatsUpdated);

        dataSource.updateData(updatedData);
        $scope.$apply();

        expect(onStatsUpdated).toHaveBeenCalledWith(
            jasmine.any(Object),
            updatedStats
        );
    });

    it('should abort active requests when requesting data that changes structure', function() {
        var deferred = $q.defer();
        deferred.promise.abort = jasmine.createSpy();
        spyOn(endpoint, 'getData').and.returnValues(
            deferred.promise,
            $q.resolve([])
        );

        dataSource.loadData();
        $scope.$apply();

        dataSource.loadData();
        $scope.$apply();
        expect(deferred.promise.abort).toHaveBeenCalled();
    });

    it('should keep active request when configuring breakdown with the same base', function() {
        dataSource.loadMetaData();
        $scope.$apply();

        spyOn(endpoint, 'getData').and.callThrough();
        var breakdowns = ['breakdown1', 'breakdown2', 'breakdown'];
        dataSource.setBreakdown(breakdowns.slice(0, 1), true);
        expect(endpoint.getData.calls.count()).toEqual(1);

        dataSource.setBreakdown(breakdowns.slice(0, 2), true);
        expect(endpoint.getData.calls.count()).toEqual(1);

        dataSource.setBreakdown(breakdowns.slice(0, 3), true);
        expect(endpoint.getData.calls.count()).toEqual(1);

        dataSource.setBreakdown(breakdowns.slice(1, 2), true);
        expect(endpoint.getData.calls.count()).toEqual(2);

        dataSource.setBreakdown(breakdowns.slice(1, 3), true);
        expect(endpoint.getData.calls.count()).toEqual(2);

        dataSource.setBreakdown(breakdowns.slice(0, 3), true);
        expect(endpoint.getData.calls.count()).toEqual(3);
    });

    it('should be able to configure different request properties', function() {
        spyOn(endpoint, 'getData').and.callThrough();
        dataSource.loadMetaData();
        $scope.$apply();

        var order = '-cost';
        var dateRange = {
            startDate: moment(new Date(2016, 1, 1)),
            endDate: moment(new Date(2016, 1, 10)),
        };
        dataSource.setFilter(dataSource.FILTER.SHOW_ARCHIVED_SOURCES, true);
        dataSource.setFilter(
            dataSource.FILTER.SHOW_BLACKLISTED_PUBLISHERS,
            true
        );
        dataSource.setFilter(dataSource.FILTER.FILTERED_MEDIA_SOURCES, [
            1,
            2,
            3,
        ]);
        dataSource.setDateRange(dateRange);
        dataSource.setOrder(order);

        expect(endpoint.getData).not.toHaveBeenCalled();
        dataSource.loadData();
        $scope.$apply();
        expect(endpoint.getData).toHaveBeenCalledWith({
            level: jasmine.any(Number),
            offset: jasmine.any(Number),
            limit: jasmine.any(Number),
            breakdown: jasmine.any(Array),
            breakdownParents: jasmine.any(Array),
            order: order,
            startDate: dateRange.startDate,
            endDate: dateRange.endDate,
            showArchived: true,
            showBlacklistedPublishers: true,
            filteredSources: [1, 2, 3],
        });
    });
});
