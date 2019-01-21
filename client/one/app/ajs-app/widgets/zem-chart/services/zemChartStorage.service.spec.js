describe('zemChartStorageService', function() {
    var $injector;
    var zemChartStorageService;
    var zemLocalStorageService;
    var zemNavigationNewService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        zemChartStorageService = $injector.get('zemChartStorageService');
        zemLocalStorageService = $injector.get('zemLocalStorageService');
        zemNavigationNewService = $injector.get('zemNavigationNewService');
    }));

    it('should load stored metrics for account if available', function() {
        var testMetrics = {metric1: 'metric1', metric2: 'metric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue({
            id: 1,
        });
        spyOn(zemLocalStorageService, 'get').and.returnValue({1: testMetrics});

        expect(zemChartStorageService.loadMetrics()).toEqual(testMetrics);
    });

    it('should load stored metrics for all accounts on all accounts level', function() {
        var testMetrics = {metric1: 'metric1', metric2: 'metric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue(
            null
        );
        spyOn(zemLocalStorageService, 'get').and.returnValue({
            allAccounts: testMetrics,
        });

        expect(zemChartStorageService.loadMetrics('all_accounts')).toEqual(
            testMetrics
        );
    });

    it('should return undefined if stored metrics for account are not available', function() {
        var testMetrics = {metric1: 'metric1', metric2: 'metric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue({
            id: 2,
        });
        spyOn(zemLocalStorageService, 'get').and.returnValue({1: testMetrics});

        expect(zemChartStorageService.loadMetrics()).toEqual(undefined);
    });

    it('should return undefined if stored metrics for all accounts level are not available', function() {
        var testMetrics = {metric1: 'metric1', metric2: 'metric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue(
            null
        );
        spyOn(zemLocalStorageService, 'get').and.returnValue({1: testMetrics});

        expect(zemChartStorageService.loadMetrics('all_accounts')).toEqual(
            undefined
        );
    });

    it('should try to store metrics for all accounts level', function() {
        var storedMetrics = {metric1: 'metric1', metric2: 'metric2'};
        var newMetrics = {metric1: 'newMetric1', metric2: 'newMetric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue(
            null
        );
        spyOn(zemLocalStorageService, 'get').and.returnValue({
            1: storedMetrics,
        });
        spyOn(zemLocalStorageService, 'set').and.stub();

        zemChartStorageService.saveMetrics(newMetrics, 'all_accounts');

        expect(zemLocalStorageService.set).toHaveBeenCalledWith(
            'metrics',
            {
                allAccounts: newMetrics,
                1: storedMetrics,
            },
            'zemChart'
        );
    });

    it('should try to store metrics for account', function() {
        var storedMetrics = {metric1: 'metric1', metric2: 'metric2'};
        var newMetrics = {metric1: 'newMetric1', metric2: 'newMetric2'};

        spyOn(zemNavigationNewService, 'getActiveAccount').and.returnValue({
            id: 1,
        });
        spyOn(zemLocalStorageService, 'get').and.returnValue({
            allAccounts: storedMetrics,
        });
        spyOn(zemLocalStorageService, 'set').and.stub();

        zemChartStorageService.saveMetrics(newMetrics);

        expect(zemLocalStorageService.set).toHaveBeenCalledWith(
            'metrics',
            {
                allAccounts: storedMetrics,
                1: newMetrics,
            },
            'zemChart'
        );
    });
});
