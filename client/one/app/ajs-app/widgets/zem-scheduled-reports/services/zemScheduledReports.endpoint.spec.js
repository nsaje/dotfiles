describe('zemScheduledReportsEndpoint', function() {
    var $injector;
    var $http;
    var zemScheduledReportsEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $http = $injector.get('$http');
        zemScheduledReportsEndpoint = $injector.get(
            'zemScheduledReportsEndpoint'
        );
    }));

    it('should make correct request to server for all accounts scheduled reports', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = null;

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);

        zemScheduledReportsEndpoint.list(entity);
        expect($http.get).toHaveBeenCalledWith('/api/all_accounts/reports/');
    });

    it('should make correct request to server for account scheduled reports', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        var entity = {
            id: 999,
            type: constants.entityType.ACCOUNT,
        };

        spyOn($http, 'get').and.callFake(mockedAsyncFunction);

        zemScheduledReportsEndpoint.list(entity);
        expect($http.get).toHaveBeenCalledWith('/api/accounts/999/reports/');
    });

    it('should make correct request to server to remove scheduled report', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );

        spyOn($http, 'delete').and.callFake(mockedAsyncFunction);

        zemScheduledReportsEndpoint.remove(123);
        expect($http.delete).toHaveBeenCalledWith(
            '/api/accounts/reports/remove/123'
        );
    });
});
