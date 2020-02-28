var RoutePathName = require('../../../../app.constants').RoutePathName;
var LevelParam = require('../../../../app.constants').LevelParam;
var BreakdownParam = require('../../../../app.constants').BreakdownParam;

describe('zemFilterSelectorService', function() {
    var $injector;
    var $httpBackend;
    var zemFilterSelectorService;
    var zemDataFilterService;
    var zemPermissions;
    var zemMediaSourcesService;
    var zemAgenciesService;
    var mockedNgRouter;

    function getVisibleConditions() {
        return zemFilterSelectorService
            .getVisibleSections()
            .map(function(section) {
                return section.condition.name;
            });
    }

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $httpBackend = $injector.get('$httpBackend');
        zemFilterSelectorService = $injector.get('zemFilterSelectorService');
        zemDataFilterService = $injector.get('zemDataFilterService');
        zemPermissions = $injector.get('zemPermissions');
        zemMediaSourcesService = $injector.get('zemMediaSourcesService');
        zemAgenciesService = $injector.get('zemAgenciesService');
        mockedNgRouter = $injector.get('NgRouter');

        zemPermissions.setMockedPermissions([
            'zemauth.can_filter_by_agency',
            'zemauth.can_filter_by_account_type',
            'zemauth.can_see_publisher_blacklist_status',
            'zemauth.can_filter_by_media_source',
        ]);

        spyOn(zemMediaSourcesService, 'getAvailableSources').and.callFake(
            zemSpecsHelper.getMockedAsyncFunction($injector, [])
        );
        spyOn(zemAgenciesService, 'getAgencies').and.callFake(
            zemSpecsHelper.getMockedAsyncFunction($injector, [])
        );

        zemFilterSelectorService.init();
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should exclude section from visible sections if user has no permission to see it', function() {
        zemPermissions.setMockedPermissions([]);

        var visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(false);
    });

    it('should include correct sections on all accounts level', function() {
        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.ACCOUNTS,
        ]);

        var visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(false);
    });

    it('should include correct sections on publishers level', function() {
        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.AD_GROUP,
            12345,
            BreakdownParam.PUBLISHERS,
        ]);

        var visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(true);
    });

    it('should include correct sections on other levels', function() {
        var visibleConditions;

        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.ACCOUNTS,
        ]);

        visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(false);

        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.CAMPAIGN,
            12345,
        ]);

        visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(false);

        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.AD_GROUP,
            12345,
        ]);

        visibleConditions = getVisibleConditions();
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.sources.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.agencies.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.accountTypes.name
            ) !== -1
        ).toBe(false);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.statuses.name
            ) !== -1
        ).toBe(true);
        expect(
            visibleConditions.indexOf(
                zemDataFilterService.CONDITIONS.publisherStatus.name
            ) !== -1
        ).toBe(false);
    });

    it('should return correctly structured applied conditions list', function() {
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            accountTypes: ['2', '3'],
            statuses: [zemDataFilterService.STATUSES_CONDITION_VALUES.archived],
            publisherStatus:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.active,
        });

        mockedNgRouter.navigate([
            RoutePathName.APP_BASE,
            RoutePathName.ANALYTICS,
            LevelParam.ACCOUNTS,
            BreakdownParam.PUBLISHERS,
        ]);

        var visibleSections = zemFilterSelectorService.getVisibleSections();
        expect(
            zemFilterSelectorService.getAppliedConditions(visibleSections)
        ).toEqual([
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

    it('should exclude unknown conditions from applied conditions list', function() {
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            unknown: 'unknown',
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([]);
    });

    it('should exclude conditions with no options from applied conditions list', function() {
        spyOn(zemDataFilterService, 'getAppliedConditions').and.returnValue({
            sources: ['1', '2', '3'],
        });

        expect(zemFilterSelectorService.getAppliedConditions()).toEqual([]);
    });

    it('should apply selected conditions', function() {
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

    it('should remove applied condition', function() {
        spyOn(zemDataFilterService, 'removeValueFromConditionList').and.stub();
        spyOn(zemDataFilterService, 'resetCondition').and.stub();

        zemFilterSelectorService.removeAppliedCondition({}, '1');
        expect(
            zemDataFilterService.removeValueFromConditionList
        ).toHaveBeenCalled();

        zemFilterSelectorService.removeAppliedCondition({});
        expect(zemDataFilterService.resetCondition).toHaveBeenCalled();
    });

    it("should correctly select all/none section's options", function() {
        var mockedSection = {
            options: [{enabled: false}, {enabled: true}],
            allOptionsSelected: false,
        };

        zemFilterSelectorService.toggleSelectAll(mockedSection);
        expect(mockedSection).toEqual({
            options: [{enabled: true}, {enabled: true}],
            allOptionsSelected: true,
        });

        zemFilterSelectorService.toggleSelectAll(mockedSection);
        expect(mockedSection).toEqual({
            options: [{enabled: false}, {enabled: false}],
            allOptionsSelected: false,
        });
    });
});
