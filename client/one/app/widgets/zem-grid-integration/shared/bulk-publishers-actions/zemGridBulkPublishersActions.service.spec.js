describe('service: zemGridBulkPublishersActionsService', function () {

    var service;
    var zemGridConstants;
    var zemDataFilterService;
    var zemGridBulkPublishersActionsEndpoint;
    var gridApi;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function ($q, _zemDataFilterService_, _zemGridBulkPublishersActionsService_, _zemGridBulkPublishersActionsEndpoint_, _zemGridConstants_, _zemGridMocks_) { // eslint-disable-line max-len
        zemDataFilterService = _zemDataFilterService_;
        zemGridBulkPublishersActionsEndpoint = _zemGridBulkPublishersActionsEndpoint_;
        zemGridConstants = _zemGridConstants_;

        zemDataFilterService.getDateRange = function () {
            return {startDate: moment('2017-01-01'), endDate: moment('2017-01-01')};
        };

        gridApi = _zemGridMocks_.createApi(constants.level.AD_GROUP, constants.breakdown.PUBLISHER);
        gridApi.getMetaData = function () {
            return {id: 1};
        };
        service = _zemGridBulkPublishersActionsService_.createInstance(gridApi);

        var defered = $q.defer();
        spyOn(zemGridBulkPublishersActionsEndpoint, 'bulkUpdate').and.returnValue(defered.promise);
    }));

    it('should call the endpoint', function () {
        var action = service.getBlacklistActions()[0];
        gridApi.getSelection = function () {
            return {
                type: zemGridConstants.gridSelectionFilterType.CUSTOM,
                selected: [{
                    data: {stats: {
                        'source_id': {value: 1},
                        'domain': {value: 'bla'},
                    }},
                    level: zemGridConstants.gridRowLevel.BASE,
                }, {
                    level: zemGridConstants.gridRowLevel.FOOTER,
                }],
                unselected: [{
                    data: {stats: {
                        'source_id': {value: 2},
                        'domain': {value: 'bla2'},
                    }},
                    level: zemGridConstants.gridRowLevel.BASE,
                }, {
                    level: zemGridConstants.gridRowLevel.LEVEL_2,
                }],
            };
        };

        service.execute(action, true);

        expect(zemGridBulkPublishersActionsEndpoint.bulkUpdate).toHaveBeenCalledWith({
            entries: [{source: 1, publisher: 'bla', include_subdomains: true}],
            entries_not_selected: [{source: 2, publisher: 'bla2', include_subdomains: undefined}],
            status: constants.publisherTargetingStatus.BLACKLISTED,
            ad_group: 1,
            level: constants.publisherBlacklistLevel.ADGROUP,
            enforce_cpc: true,
            select_all: false,
            start_date: '2017-01-01',
            end_date: '2017-01-01',
        });
    });

    it('should call the endpoint with select all flag and without enforcing cpc constraints', function () {
        var action = service.getBlacklistActions()[1];
        gridApi.getSelection = function () {
            return {
                type: zemGridConstants.gridSelectionFilterType.ALL,
                selected: [],
                unselected: [],
            };
        };

        service.execute(action, false);

        expect(zemGridBulkPublishersActionsEndpoint.bulkUpdate).toHaveBeenCalledWith({
            entries: [],
            entries_not_selected: [],
            status: constants.publisherTargetingStatus.BLACKLISTED,
            ad_group: 1,
            level: constants.publisherBlacklistLevel.CAMPAIGN,
            enforce_cpc: false,
            select_all: true,
            start_date: '2017-01-01',
            end_date: '2017-01-01',
        });
    });
});
