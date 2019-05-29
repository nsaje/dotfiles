describe('zemInfoboxEndpoint', function() {
    var $injector;
    var $http;
    var zemInfoboxEndpoint;
    var zemDataFilterService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $http = $injector.get('$http');
        zemInfoboxEndpoint = $injector.get('zemInfoboxEndpoint');
        zemDataFilterService = $injector.get('zemDataFilterService');
    }));

    it('should make correct request to server for all accounts', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = null;
        var dateRange = {
            startDate: moment('2017-01-01'),
            endDate: moment('2017-01-01'),
        };
        var filteredAgencies = [1, 2, 3];
        var filteredAccountTypes = [4, 5, 6];
        var filteredBusinesses = [7, 8];

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);
        spyOn(zemDataFilterService, 'getDateRange').and.returnValue(dateRange);
        spyOn(zemDataFilterService, 'getFilteredAgencies').and.returnValue(
            filteredAgencies
        );
        spyOn(zemDataFilterService, 'getFilteredAccountTypes').and.returnValue(
            filteredAccountTypes
        );
        spyOn(zemDataFilterService, 'getFilteredBusinesses').and.returnValue(
            filteredBusinesses
        );

        zemInfoboxEndpoint.getInfoboxData(entity);
        expect($http.get).toHaveBeenCalledWith('/api/accounts/overview/', {
            params: {
                start_date: dateRange.startDate.format('YYYY-MM-DD'),
                end_date: dateRange.endDate.format('YYYY-MM-DD'),
                filtered_agencies: filteredAgencies.join(','),
                filtered_account_types: filteredAccountTypes.join(','),
                filtered_businesses: filteredBusinesses,
            },
        });
    });

    it('should make correct request to server for account entity', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = {
            id: 999,
            type: constants.entityType.ACCOUNT,
        };
        var dateRange = {
            startDate: moment('2017-01-01'),
            endDate: moment('2017-01-01'),
        };

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);
        spyOn(zemDataFilterService, 'getDateRange').and.returnValue(dateRange);

        zemInfoboxEndpoint.getInfoboxData(entity);
        expect($http.get).toHaveBeenCalledWith('/api/accounts/999/overview/', {
            params: {
                start_date: dateRange.startDate.format('YYYY-MM-DD'),
                end_date: dateRange.endDate.format('YYYY-MM-DD'),
            },
        });
    });

    it('should make correct request to server for campaign entity', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = {
            id: 999,
            type: constants.entityType.CAMPAIGN,
        };
        var dateRange = {
            startDate: moment('2017-01-01'),
            endDate: moment('2017-01-01'),
        };

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);
        spyOn(zemDataFilterService, 'getDateRange').and.returnValue(dateRange);

        zemInfoboxEndpoint.getInfoboxData(entity);
        expect($http.get).toHaveBeenCalledWith('/api/campaigns/999/overview/', {
            params: {
                start_date: dateRange.startDate.format('YYYY-MM-DD'),
                end_date: dateRange.endDate.format('YYYY-MM-DD'),
            },
        });
    });

    it('should make correct request to server for ad group entity', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = {
            id: 999,
            type: constants.entityType.AD_GROUP,
        };
        var dateRange = {
            startDate: moment('2017-01-01'),
            endDate: moment('2017-01-01'),
        };
        var filteredSources = [1, 2, 3];

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);
        spyOn(zemDataFilterService, 'getDateRange').and.returnValue(dateRange);
        spyOn(zemDataFilterService, 'getFilteredSources').and.returnValue(
            filteredSources
        );

        zemInfoboxEndpoint.getInfoboxData(entity);
        expect($http.get).toHaveBeenCalledWith('/api/ad_groups/999/overview/', {
            params: {
                start_date: dateRange.startDate.format('YYYY-MM-DD'),
                end_date: dateRange.endDate.format('YYYY-MM-DD'),
                filtered_sources: filteredSources.join(','),
            },
        });
    });
});
