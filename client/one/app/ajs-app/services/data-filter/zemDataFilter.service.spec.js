describe('zemDataFilterService', function() {
    var $location;
    var zemDataFilterService;
    var zemPermissions;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));
    beforeEach(inject(function(
        _$location_,
        _zemDataFilterService_,
        _zemPermissions_
    ) {
        $location = _$location_;
        zemDataFilterService = _zemDataFilterService_;
        zemPermissions = _zemPermissions_;

        zemPermissions.setMockedPermissions([
            'zemauth.can_see_publishers',
            'zemauth.can_filter_by_agency',
            'zemauth.can_filter_by_account_type',
        ]);
    }));

    it('should init correctly with default values', function() {
        var today = moment('2016-01-05').toDate();
        jasmine.clock().mockDate(today);

        zemDataFilterService.init();

        var dateRange = zemDataFilterService.getDateRange();
        expect(dateRange.startDate.valueOf()).toEqual(
            moment('2016-01-01')
                .startOf('day')
                .valueOf()
        );
        expect(dateRange.endDate.valueOf()).toEqual(
            moment('2016-01-31')
                .endOf('day')
                .valueOf()
        );

        var expectedConditions = {};
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );
    });

    it('should init correctly with url params', function() {
        spyOn($location, 'search').and.returnValue({
            replace: angular.noop,
            start_date: moment('2016-11-01').format('YYYY-MM-DD'),
            end_date: moment('2016-12-01').format('YYYY-MM-DD'),
            filtered_sources: '1,2',
            filtered_agencies: '3,4',
            filtered_account_types: '5,6',
            filtered_statuses:
                zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
            filtered_publisher_status:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.active,
        });

        zemDataFilterService.init();

        var dateRange = zemDataFilterService.getDateRange();
        expect(dateRange.startDate.valueOf()).toEqual(
            moment('2016-11-01').valueOf()
        );
        expect(dateRange.endDate.valueOf()).toEqual(
            moment('2016-12-01').valueOf()
        );

        var expectedConditions = {};
        expectedConditions[zemDataFilterService.CONDITIONS.sources.name] = [
            '1',
            '2',
        ];
        expectedConditions[zemDataFilterService.CONDITIONS.agencies.name] = [
            '3',
            '4',
        ];
        expectedConditions[
            zemDataFilterService.CONDITIONS.accountTypes.name
        ] = ['5', '6'];
        expectedConditions[zemDataFilterService.CONDITIONS.statuses.name] = [
            zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
        ]; // eslint-disable-line max-len
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.active; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );
    });

    it("shouldn't init with url params if user doesn't have permissions", function() {
        spyOn($location, 'search').and.returnValue({
            filtered_publisher_status:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.active,
        });
        zemPermissions.setMockedPermissions([]);

        zemDataFilterService.init();

        var expectedConditions = {};
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );
    });

    it('should correctly set date range', function() {
        var dateRange = {
            startDate: moment('2015-12-03'),
            endDate: moment('2015-12-31'),
        };
        zemDataFilterService.setDateRange(dateRange);

        var updatedDateRange = zemDataFilterService.getDateRange();
        expect(updatedDateRange.startDate.valueOf()).toEqual(
            dateRange.startDate.valueOf()
        );
        expect(updatedDateRange.endDate.valueOf()).toEqual(
            dateRange.endDate.valueOf()
        );
    });

    it('should return undefined if requested condition does not exist', function() {
        expect(zemDataFilterService.getAppliedCondition()).toEqual(undefined);
    });

    it('should return empty condition if requested condition is not set', function() {
        expect(zemDataFilterService.getFilteredSources()).toEqual([]);
    });

    it('should correctly return applied conditions and exclude conditions with default values', function() {
        zemDataFilterService.init();

        var expectedConditions = {};
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );
        expect(zemDataFilterService.getAppliedConditions(true)).toEqual({});
    });

    it('should correctly apply conditions', function() {
        var conditions = [
            {
                condition: zemDataFilterService.CONDITIONS.sources,
                value: ['1'],
            },
            {
                condition: zemDataFilterService.CONDITIONS.agencies,
                value: ['2', '3'],
            },
            {
                condition: zemDataFilterService.CONDITIONS.accountTypes,
                value: ['4', '5', '6'],
            },
            {
                condition: zemDataFilterService.CONDITIONS.statuses,
                value: [
                    zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
                ],
            },
            {
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                        .blacklisted,
            },
        ];
        zemDataFilterService.applyConditions(conditions);

        var expectedConditions = {};
        expectedConditions[zemDataFilterService.CONDITIONS.sources.name] = [
            '1',
        ];
        expectedConditions[zemDataFilterService.CONDITIONS.agencies.name] = [
            '2',
            '3',
        ];
        expectedConditions[
            zemDataFilterService.CONDITIONS.accountTypes.name
        ] = ['4', '5', '6'];
        expectedConditions[zemDataFilterService.CONDITIONS.statuses.name] = [
            zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
        ]; // eslint-disable-line max-len
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.blacklisted; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );
        expect($location.search()).toEqual({
            filtered_sources: '1',
            filtered_agencies: '2,3',
            filtered_account_types: '4,5,6',
            filtered_statuses:
                zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
            filtered_publisher_status:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                    .blacklisted,
        });
    });

    it('should reset condition to its default value', function() {
        var conditions = [
            {
                condition: zemDataFilterService.CONDITIONS.sources,
                value: ['1'],
            },
            {
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                        .blacklisted,
            },
        ];
        zemDataFilterService.applyConditions(conditions);

        var expectedConditions = {};
        expectedConditions[zemDataFilterService.CONDITIONS.sources.name] = [
            '1',
        ];
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.blacklisted; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );

        zemDataFilterService.resetCondition(
            zemDataFilterService.CONDITIONS.sources
        );
        expect(zemDataFilterService.getFilteredSources()).toEqual([]);

        zemDataFilterService.resetCondition(
            zemDataFilterService.CONDITIONS.publisherStatus
        );
        expect(zemDataFilterService.getFilteredPublisherStatus()).toEqual(
            zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all
        );
        expect($location.search()).toEqual({
            filtered_publisher_status:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all,
        });
    });

    it('should reset all conditions to their default value', function() {
        var conditions = [
            {
                condition: zemDataFilterService.CONDITIONS.sources,
                value: ['1'],
            },
            {
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                        .blacklisted,
            },
        ];
        zemDataFilterService.applyConditions(conditions);

        var expectedConditions = {};
        expectedConditions[zemDataFilterService.CONDITIONS.sources.name] = [
            '1',
        ];
        expectedConditions[
            zemDataFilterService.CONDITIONS.publisherStatus.name
        ] = zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.blacklisted; // eslint-disable-line max-len
        expect(zemDataFilterService.getAppliedConditions()).toEqual(
            expectedConditions
        );

        zemDataFilterService.resetAllConditions();
        expect(zemDataFilterService.getFilteredSources()).toEqual([]);
        expect(zemDataFilterService.getFilteredPublisherStatus()).toEqual(
            zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all
        );
        expect($location.search()).toEqual({
            filtered_publisher_status:
                zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all,
        });
    });

    it("should remove value from condition's list if it exists", function() {
        var conditions = [
            {
                condition: zemDataFilterService.CONDITIONS.sources,
                value: ['1', '2', '3'],
            },
        ];
        zemDataFilterService.applyConditions(conditions);
        expect(zemDataFilterService.getFilteredSources()).toEqual([
            '1',
            '2',
            '3',
        ]);
        expect($location.search()).toEqual({
            filtered_sources: '1,2,3',
        });

        zemDataFilterService.removeValueFromConditionList(
            zemDataFilterService.CONDITIONS.sources,
            '3'
        );
        expect(zemDataFilterService.getFilteredSources()).toEqual(['1', '2']);
        expect($location.search()).toEqual({
            filtered_sources: '1,2',
        });

        zemDataFilterService.removeValueFromConditionList(
            zemDataFilterService.CONDITIONS.sources,
            'unknown'
        );
        expect(zemDataFilterService.getFilteredSources()).toEqual(['1', '2']);
        expect($location.search()).toEqual({
            filtered_sources: '1,2',
        });
    });

    it('should correctly return if archived entities are shown', function() {
        var conditions = [
            {
                condition: zemDataFilterService.CONDITIONS.statuses,
                value: [
                    zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
                ],
            },
        ];
        zemDataFilterService.applyConditions(conditions);
        expect(zemDataFilterService.getShowArchived()).toEqual(true);
        zemDataFilterService.resetAllConditions();
        expect(zemDataFilterService.getShowArchived()).toEqual(false);
    });
});
