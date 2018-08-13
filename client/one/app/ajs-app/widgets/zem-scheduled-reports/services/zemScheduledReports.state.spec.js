describe('zemScheduledReportsStateService', function() {
    var $injector;
    var $rootScope;
    var $httpBackend;
    var zemScheduledReportsStateService;
    var zemScheduledReportsEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $rootScope = $injector.get('$rootScope');
        $httpBackend = $injector.get('$httpBackend');
        zemScheduledReportsStateService = $injector.get(
            'zemScheduledReportsStateService'
        );
        zemScheduledReportsEndpoint = $injector.get(
            'zemScheduledReportsEndpoint'
        );

        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    it('should create new state instance', function() {
        var stateService = zemScheduledReportsStateService.createInstance();
        expect(stateService.getState).toBeDefined();
    });

    it('should correctly update state when successfully getting data from endpoint', function() {
        var reports = [{id: 1}, {id: 2}];
        var stateService = zemScheduledReportsStateService.createInstance({
            id: 999,
            type: 'mockedAccount',
        });
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            reports
        );

        spyOn(zemScheduledReportsEndpoint, 'list').and.callFake(
            mockedAsyncFunction
        );

        stateService.reloadReports();
        expect(stateService.getState()).toEqual({
            loadReportsRequestInProgress: true,
        });
        $rootScope.$digest();
        expect(stateService.getState()).toEqual({
            reports: reports,
            loadReportsRequestInProgress: false,
        });
    });

    it('should correctly update state when unsuccessfully getting data from endpoint', function() {
        var stateService = zemScheduledReportsStateService.createInstance({
            id: 999,
            type: 'mockedAccount',
        });
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            'error',
            true
        );

        spyOn(zemScheduledReportsEndpoint, 'list').and.callFake(
            mockedAsyncFunction
        );

        stateService.reloadReports();
        expect(stateService.getState()).toEqual({
            loadReportsRequestInProgress: true,
        });
        $rootScope.$digest();
        expect(stateService.getState()).toEqual({
            loadErrorMessage: 'Error retrieving reports',
            loadReportsRequestInProgress: false,
        });
    });

    it('should make a correct request to endpoint when removing report and reload state on success', function() {
        var stateService = zemScheduledReportsStateService.createInstance({
            id: 999,
            type: 'mockedAccount',
        });
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );

        spyOn(stateService, 'reloadReports').and.stub();
        spyOn(zemScheduledReportsEndpoint, 'remove').and.callFake(
            mockedAsyncFunction
        );

        stateService.removeReport({scheduledReportId: 123});
        expect(stateService.getState()).toEqual({
            removeRequestInProgress: true,
        });
        $rootScope.$digest();
        expect(zemScheduledReportsEndpoint.remove).toHaveBeenCalledWith(123);
        expect(stateService.reloadReports).toHaveBeenCalled();
    });

    it('should make a correct request to endpoint when removing report and set error message on failure', function() {
        var stateService = zemScheduledReportsStateService.createInstance({
            id: 999,
            type: 'mockedAccount',
        });
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            {},
            true
        );

        spyOn(stateService, 'reloadReports').and.stub();
        spyOn(zemScheduledReportsEndpoint, 'remove').and.callFake(
            mockedAsyncFunction
        );

        stateService.removeReport({scheduledReportId: 123});
        expect(stateService.getState()).toEqual({
            removeRequestInProgress: true,
        });
        $rootScope.$digest();
        expect(zemScheduledReportsEndpoint.remove).toHaveBeenCalledWith(123);
        expect(stateService.reloadReports).not.toHaveBeenCalled();
        expect(stateService.getState()).toEqual({
            removeErrorMessage:
                'Error removing report. Please contact support.',
            removeRequestInProgress: false,
        });
    });
});
