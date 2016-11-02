describe('zemFilterSelectorService', function () {
    var $injector;
    var $rootScope;
    var $httpBackend;
    var $state;
    var zemFilterSelectorService;
    var zemDataFilterService;
    var zemUserService;
    var zemPermissions;
    var zemNavigationService;
    var zemMediaSourcesService;
    var zemAgenciesService;
    var mockedAsyncFunction;

    function getVisibleConditions () {
        return zemFilterSelectorService.getVisibleSections().map(function (section) {
            return section.condition.name;
        });
    }

    beforeEach(module('one'));
    beforeEach(inject(function (_$injector_) {
        $injector = _$injector_;
        $rootScope = $injector.get('$rootScope');
        $httpBackend = $injector.get('$httpBackend');
        $state = $injector.get('$state');
        zemFilterSelectorService = $injector.get('zemFilterSelectorService');
        zemDataFilterService = $injector.get('zemDataFilterService');
        zemUserService = $injector.get('zemUserService');
        zemPermissions = $injector.get('zemPermissions');
        zemNavigationService = $injector.get('zemNavigationService');
        zemMediaSourcesService = $injector.get('zemMediaSourcesService');
        zemAgenciesService = $injector.get('zemAgenciesService');

        zemSpecsHelper.mockUserInitialization($injector);
        mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction($injector);

        spyOn(zemMediaSourcesService, 'getAvailableSources').and.callFake(
            zemSpecsHelper.getMockedAsyncFunction($injector, [])
        );
        spyOn(zemAgenciesService, 'getAgencies').and.callFake(
            zemSpecsHelper.getMockedAsyncFunction($injector, [])
        );

        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});

        zemFilterSelectorService.init();
        $httpBackend.flush();
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should exclude section from visible sections if user has no permission to see it', function () {
        spyOn($state, 'includes').and.returnValue(true);

        var visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(false);

    });

    it('should include section in visible sections if user has the permission to see it', function () {
        spyOn($state, 'includes').and.returnValue(true);
        spyOn(zemUserService, 'current').and.returnValue({
            permissions: {
                'zemauth.can_filter_by_agency': true,
                'zemauth.can_filter_by_account_type': true,
                'zemauth.can_see_publisher_blacklist_status': true,
            },
        });

        var visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(true);
    });

    it('should include correct sections on all accounts level', function () {
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);

        $state.go('main.allAccounts');
        $rootScope.$apply();
        var visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(false);
    });

    it('should include correct sections on publishers level', function () {
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemNavigationService, 'getAdGroup').and.callFake(mockedAsyncFunction);

        $state.go('main.adGroups.publishers');
        $rootScope.$apply();
        var visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(true);
    });

    it('should include correct sections on other levels', function () {
        var visibleConditions;
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemNavigationService, 'getAccount').and.callFake(mockedAsyncFunction);
        spyOn(zemNavigationService, 'getCampaign').and.callFake(mockedAsyncFunction);
        spyOn(zemNavigationService, 'getAdGroup').and.callFake(mockedAsyncFunction);

        $state.go('main.accounts');
        $rootScope.$apply();
        visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(false);

        $state.go('main.campaigns');
        $rootScope.$apply();
        visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(false);

        $state.go('main.adGroups');
        $rootScope.$apply();
        visibleConditions = getVisibleConditions();
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.sources.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.agencies.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.accountTypes.name) !== -1).toBe(false);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.statuses.name) !== -1).toBe(true);
        expect(visibleConditions.indexOf(zemDataFilterService.CONDITIONS.publisherStatus.name) !== -1).toBe(false);
    });

    it('should return correctly structured applied conditions list', function () {
        spyOn($state, 'includes').and.returnValue(true);
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            accountTypes: ['2', '3'],
            statuses: [zemDataFilterService.STATUSES_CONDITION_VALUES.archived],
            publisherStatus: zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.active,
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([
            {
                name: 'Account type',
                text: 'Test',
                value: '2',
                condition: zemDataFilterService.CONDITIONS.accountTypes,
            },
            {
                name: 'Account type',
                text: 'Sandbox',
                value: '3',
                condition: zemDataFilterService.CONDITIONS.accountTypes,
            },
            {
                name: 'Status',
                text: 'Show archived',
                value: zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
                condition: zemDataFilterService.CONDITIONS.statuses,
            },
            {
                name: 'Publisher status',
                text: 'Active',
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
            },
        ]);
    });

    it('should exclude conditions set to condition\'s default value from applied conditions list', function () {
        spyOn($state, 'includes').and.returnValue(true);
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            publisherStatus: zemDataFilterService.CONDITIONS.publisherStatus.default,
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([]);
    });

    it('should exclude unknown conditions from applied conditions list', function () {
        spyOn($state, 'includes').and.returnValue(true);
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            unknown: 'unknown',
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([]);
    });

    it('should exclude conditions with no options from applied conditions list', function () {
        spyOn($state, 'includes').and.returnValue(true);
        spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            sources: ['1', '2', '3'],
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([]);
    });

    it('should apply selected conditions', function () {
        spyOn(zemDataFilterService, 'applyConditions').and.stub();

        zemFilterSelectorService.applyFilter([
            {
                condition: {type: zemDataFilterService.CONDITION_TYPES.value},
                value: 'test value',
            },
            {
                condition: {type: zemDataFilterService.CONDITION_TYPES.list},
                options: [
                    {
                        enabled: true,
                        value: 'a',
                    },
                    {
                        enabled: true,
                        value: 'b',
                    },
                    {
                        enabled: false,
                        value: 'c',
                    },
                ],
            },
        ]);

        expect(zemDataFilterService.applyConditions).toHaveBeenCalledWith([
            {
                condition: jasmine.any(Object),
                value: 'test value',
            },
            {
                condition: jasmine.any(Object),
                value: ['a', 'b'],
            },
        ]);
    });

    it('should remove applied condition', function () {
        spyOn(zemDataFilterService, 'removeValueFromConditionList').and.stub();
        spyOn(zemDataFilterService, 'resetCondition').and.stub();

        zemFilterSelectorService.removeAppliedCondition({}, '1');
        expect(zemDataFilterService.removeValueFromConditionList).toHaveBeenCalled();

        zemFilterSelectorService.removeAppliedCondition({});
        expect(zemDataFilterService.resetCondition).toHaveBeenCalled();
    });
});
