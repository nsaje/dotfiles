/* globals angular, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemDataSource', function () {
    var $scope;
    var $q;
    var $timeout;
    var dataSource;
    var endpoint;

    beforeEach(module('one'));

    beforeEach(inject(function ($httpBackend) {
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    beforeEach(inject(function ($rootScope, _$q_, _$timeout_, zemDataSourceService, zemGridDebugEndpoint) { // eslint-disable-line max-len
        $scope = $rootScope.$new();
        $q = _$q_;
        $timeout = _$timeout_;
        endpoint = zemGridDebugEndpoint.createEndpoint();
        dataSource = zemDataSourceService.createInstance(endpoint);
    }));

    it('should request meta data from endpoint if needed', function () {
        spyOn(endpoint, 'getMetaData').and.callThrough();

        dataSource.getMetaData();
        $scope.$apply();
        expect(endpoint.getMetaData).toHaveBeenCalled();

        endpoint.getMetaData.calls.reset();
        dataSource.getMetaData();
        $scope.$apply();
        expect(endpoint.getMetaData).not.toHaveBeenCalled();

        dataSource.getMetaData(true);
        $scope.$apply();
        expect(endpoint.getMetaData).toHaveBeenCalled();
    });

    it('should request data from endpoint', function () {
        spyOn(endpoint, 'getMetaData').and.callThrough();
        spyOn(endpoint, 'getData').and.callThrough();
        dataSource.getData();
        $scope.$apply();

        expect(endpoint.getMetaData).toHaveBeenCalled();
        expect(endpoint.getData).toHaveBeenCalled();

        endpoint.getMetaData.calls.reset();
        endpoint.getData.calls.reset();

        dataSource.getData();
        $scope.$apply();
        expect(endpoint.getMetaData).not.toHaveBeenCalled();
        expect(endpoint.getData).toHaveBeenCalled();
    });

    it('should notify listeners before and after applying data', function () {
        var onLoadListener = jasmine.createSpy();
        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onLoad($scope, onLoadListener);
        dataSource.onDataUpdated($scope, onDataUpdatedListener);

        dataSource.getData();
        $scope.$apply();
        $timeout.flush();

        expect(onLoadListener).toHaveBeenCalled();
        expect(onDataUpdatedListener).toHaveBeenCalled();
    });

    it('should initialize root when requesting base level data', function () {
        dataSource.getData();
        $scope.$apply();

        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onDataUpdated($scope, onDataUpdatedListener);
        dataSource.getData();

        var emptyBreakdownRoot = {
            breakdown: null,
            stats: null,
            level: 0,
            meta: {}
        };
        expect(onDataUpdatedListener).toHaveBeenCalledWith(jasmine.any(Object), emptyBreakdownRoot);
    });

    it('should build breakdown tree through sequential requests', function () {
        // Level 1 (base level) breakdown
        var breakdownL1 = {
            breakdownId: 1,
            level: 1,
            pagination: {
                offset: 0,
                limit: 2,
            },
            rows: [{breakdownId: 11}, {breakdownId: 12}],
            totals: [1, 2, 3]
        };

        // Level 2 breakdowns
        var breakdownL21 = {
            breakdownId: 11,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            rows: [{}]
        };
        var breakdownL22 = {
            breakdownId: 12,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            rows: [{}]
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
                                complete: undefined
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
                                complete: undefined
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
        dataSource.getMetaData();
        $scope.$apply();
        dataSource.setBreakdown([{}, {}]);

        // Initialize listeners and request data
        var onLoadListener = jasmine.createSpy();
        var onDataUpdatedListener = jasmine.createSpy();
        dataSource.onLoad($scope, onLoadListener);
        dataSource.onDataUpdated($scope, onDataUpdatedListener);
        dataSource.getData();
        $scope.$apply();

        // Check if everything has been notified with correct structures
        expect(onLoadListener).toHaveBeenCalledWith(jasmine.any(Object), breakdownL1);
        expect(onLoadListener).toHaveBeenCalledWith(jasmine.any(Object), breakdownL21);
        expect(onLoadListener).toHaveBeenCalledWith(jasmine.any(Object), breakdownL22);
        expect(onDataUpdatedListener).toHaveBeenCalledWith(jasmine.any(Object), breakdownRoot);
    });

    it('should be able to request data by breakdown and size', function () {
        spyOn(endpoint, 'getData').and.returnValue($q.resolve([]));
        var breakdown = {
            breakdownId: 11,
            level: 2,
            pagination: {
                offset: 0,
                limit: 1,
            },
            meta: {loading: false},
            rows: [{}]
        };

        dataSource.getData(breakdown, 10);
        $scope.$apply();

        expect(endpoint.getData).toHaveBeenCalledWith({
            level: 2,
            offset: 1,
            limit: 10,
            breakdownPage: [11],
            breakdown: jasmine.any(Array),
            order: jasmine.any(String)
        });
    });

    it('should save data using endpoint', function () {
        var value = 1;
        var column = {field: 'field2'};
        var row = {
            stats: {
                field1: {},
                field2: {},
                field3: {},
            }
        };
        var result = {value: 1};

        spyOn(endpoint, 'saveData').and.returnValue($q.resolve(result));
        var onStatsUpdated = jasmine.createSpy();
        dataSource.onStatsUpdated($scope, onStatsUpdated);

        dataSource.saveData(value, row, column);
        $scope.$apply();

        expect(endpoint.saveData).toHaveBeenCalledWith(value, row, column);
        expect(onStatsUpdated).toHaveBeenCalledWith(jasmine.any(Object), {
            stats: {
                field1: {},
                field2: {value: 1},
                field3: {},
            }
        });
    });
    it('should abort active requests when requesting data that changes structure', function () {
        var deferred = $q.defer();
        deferred.promise.abort = jasmine.createSpy();
        spyOn(endpoint, 'getData').and.returnValues(
            deferred.promise, $q.resolve([])
        );

        dataSource.getData();
        $scope.$apply();

        dataSource.getData();
        $scope.$apply();
        expect(deferred.promise.abort).toHaveBeenCalled();
    });

    it('should keep active request when configuring breakdown with the same base', function () {
        dataSource.getMetaData();
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

    it('should be able to configure different request properties', function () {
        spyOn(endpoint, 'getData').and.callThrough();
        dataSource.getMetaData();
        $scope.$apply();

        var order = '-cost';
        var dateRange = {
            startDate: new Date(2016, 1, 1),
            endDate: new Date(2016, 1, 10),
        };
        dataSource.setFilter(dataSource.FILTER.SHOW_ARCHIVED_SOURCES, true);
        dataSource.setFilter(dataSource.FILTER.SHOW_BLACKLISTED_PUBLISHERS, true);
        dataSource.setFilter(dataSource.FILTER.FILTERED_MEDIA_SOURCES, [1, 2, 3]);
        dataSource.setDateRange(dateRange);
        dataSource.setOrder(order);

        expect(endpoint.getData).not.toHaveBeenCalled();
        dataSource.getData();
        $scope.$apply();
        expect(endpoint.getData).toHaveBeenCalledWith({
            level: jasmine.any(Number),
            offset: jasmine.any(Number),
            limit: jasmine.any(Number),
            breakdown: jasmine.any(Array),
            breakdownPage: jasmine.any(Array),
            order: order,
            startDate: dateRange.startDate,
            endDate: dateRange.endDate,
            showArchived: true,
            showBlacklistedPublishers: true,
            filteredSources: [1, 2, 3],
        });
    });

});

