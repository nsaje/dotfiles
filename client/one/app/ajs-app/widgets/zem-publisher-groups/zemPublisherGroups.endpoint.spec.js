describe('component: zemPublisherGroupsEndpoint', function() {
    var $injector;
    var $http;
    var zemPublisherGroupsEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        _$injector_,
        _$http_,
        _zemPublisherGroupsEndpoint_
    ) {
        $injector = _$injector_;
        $http = _$http_;
        zemPublisherGroupsEndpoint = _zemPublisherGroupsEndpoint_;
    }));

    it('should make correct request for get publisher groups', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        spyOn($http, 'get').and.callFake(mockedAsyncFunction);

        zemPublisherGroupsEndpoint.list(1, null);

        expect($http.get).toHaveBeenCalledWith(
            '/api/accounts/1/publisher_groups/',
            {
                params: {
                    not_implicit: undefined,
                },
            }
        );
    });

    it('should make correct request for create new publisher group', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );
        spyOn($http, 'post').and.callFake(mockedAsyncFunction);

        zemPublisherGroupsEndpoint.upsert({
            name: 'asd',
            include_subdomains: true,
            file: {},
            accountId: 1,
        });

        var formData = new FormData();
        formData.append('name', 'asd');
        formData.append('include_subdomains', true);
        formData.append('entries', {});

        expect($http.post).toHaveBeenCalledWith(
            '/api/accounts/1/publisher_groups/upload/',
            formData,
            {
                transformRequest: angular.identity,
                headers: {'Content-Type': undefined},
            }
        );
    });
});
