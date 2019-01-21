describe('service: zemGridBulkPublishersActionsService', function() {
    var zemGridBulkPublishersActionsService;
    var zemGridConstants;
    var zemDataFilterService;
    var zemGridBulkPublishersActionsEndpoint;
    var zemNavigationNewService;
    var selection;

    function getExpectedEndpointParams(override) {
        var params = {
            entries: [{source: 1, publisher: 'bla', include_subdomains: true}],
            entries_not_selected: [
                {source: 2, publisher: 'bla2', include_subdomains: undefined},
            ],
            status: constants.publisherTargetingStatus.BLACKLISTED,
            enforce_cpc: true,
            select_all: false,
            start_date: '2017-01-01',
            end_date: '2017-01-01',
        };
        if (override) {
            angular.extend(params, override);
        }
        return params;
    }

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        $q,
        _zemDataFilterService_,
        _zemGridBulkPublishersActionsService_,
        _zemGridBulkPublishersActionsEndpoint_,
        _zemGridConstants_,
        _zemGridMocks_,
        _zemNavigationNewService_
    ) {
        // eslint-disable-line max-len
        zemDataFilterService = _zemDataFilterService_;
        zemGridBulkPublishersActionsEndpoint = _zemGridBulkPublishersActionsEndpoint_;
        zemGridConstants = _zemGridConstants_;
        zemNavigationNewService = _zemNavigationNewService_;
        zemGridBulkPublishersActionsService = _zemGridBulkPublishersActionsService_;

        zemDataFilterService.getDateRange = function() {
            return {
                startDate: moment('2017-01-01'),
                endDate: moment('2017-01-01'),
            };
        };

        selection = {
            type: zemGridConstants.gridSelectionFilterType.CUSTOM,
            selected: [
                {
                    data: {
                        stats: {
                            source_id: {value: 1},
                            domain: {value: 'bla'},
                        },
                    },
                    level: zemGridConstants.gridRowLevel.BASE,
                },
                {
                    level: zemGridConstants.gridRowLevel.FOOTER,
                },
            ],
            unselected: [
                {
                    data: {
                        stats: {
                            source_id: {value: 2},
                            domain: {value: 'bla2'},
                        },
                    },
                    level: zemGridConstants.gridRowLevel.BASE,
                },
                {
                    level: zemGridConstants.gridRowLevel.LEVEL_2,
                },
            ],
        };

        spyOn(zemNavigationNewService, 'getActiveEntityByType').and.returnValue(
            {
                id: 1,
            }
        );

        var defered = $q.defer();
        spyOn(
            zemGridBulkPublishersActionsEndpoint,
            'bulkUpdate'
        ).and.returnValue(defered.promise);
    }));

    it('should call the endpoint for adgroup', function() {
        var action = zemGridBulkPublishersActionsService.getBlacklistActions(
            constants.level.AD_GROUPS
        )[0];

        zemGridBulkPublishersActionsService.execute(action, true, selection);

        expect(
            zemGridBulkPublishersActionsEndpoint.bulkUpdate
        ).toHaveBeenCalledWith(getExpectedEndpointParams({ad_group: 1}));
        expect(
            zemNavigationNewService.getActiveEntityByType
        ).toHaveBeenCalledWith('adGroup');
    });

    it('should call the endpoint for campaign', function() {
        var action = zemGridBulkPublishersActionsService.getBlacklistActions(
            constants.level.AD_GROUPS
        )[1];

        zemGridBulkPublishersActionsService.execute(action, true, selection);

        expect(
            zemGridBulkPublishersActionsEndpoint.bulkUpdate
        ).toHaveBeenCalledWith(getExpectedEndpointParams({campaign: 1}));
        expect(
            zemNavigationNewService.getActiveEntityByType
        ).toHaveBeenCalledWith('campaign');
    });

    it('should call the endpoint for account', function() {
        var action = zemGridBulkPublishersActionsService.getBlacklistActions(
            constants.level.AD_GROUPS
        )[2];

        zemGridBulkPublishersActionsService.execute(action, true, selection);

        expect(
            zemGridBulkPublishersActionsEndpoint.bulkUpdate
        ).toHaveBeenCalledWith(getExpectedEndpointParams({account: 1}));
        expect(
            zemNavigationNewService.getActiveEntityByType
        ).toHaveBeenCalledWith('account');
    });

    it('should call the endpoint for global blacklist', function() {
        var action = zemGridBulkPublishersActionsService.getBlacklistActions(
            constants.level.AD_GROUPS
        )[3];

        zemGridBulkPublishersActionsService.execute(action, true, selection);

        expect(
            zemGridBulkPublishersActionsEndpoint.bulkUpdate
        ).toHaveBeenCalledWith(getExpectedEndpointParams());
        expect(
            zemNavigationNewService.getActiveEntityByType
        ).not.toHaveBeenCalled();
    });

    it('should call the endpoint with select all flag and without enforcing cpc constraints', function() {
        var action = zemGridBulkPublishersActionsService.getBlacklistActions(
            constants.level.AD_GROUPS
        )[1];

        selection = {
            type: zemGridConstants.gridSelectionFilterType.ALL,
            selected: [],
            unselected: [],
        };

        zemGridBulkPublishersActionsService.execute(action, false, selection);

        expect(
            zemGridBulkPublishersActionsEndpoint.bulkUpdate
        ).toHaveBeenCalledWith({
            entries: [],
            entries_not_selected: [],
            status: constants.publisherTargetingStatus.BLACKLISTED,
            campaign: 1,
            enforce_cpc: false,
            select_all: true,
            start_date: '2017-01-01',
            end_date: '2017-01-01',
        });
        expect(
            zemNavigationNewService.getActiveEntityByType
        ).toHaveBeenCalledWith('campaign');
    });
});
