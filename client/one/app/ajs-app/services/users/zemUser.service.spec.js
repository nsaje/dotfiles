describe('zemUserService', function() {
    var $rootScope;
    var zemUserService;
    var mockedUser = {
        id: 123,
        email: 'test@zemanta.com',
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        _$rootScope_,
        $q,
        _zemUserService_,
        zemUserEndpoint
    ) {
        $rootScope = _$rootScope_;
        zemUserService = _zemUserService_;

        spyOn(zemUserEndpoint, 'current').and.callFake(function() {
            var deferred = $q.defer();
            deferred.resolve(mockedUser);
            return deferred.promise;
        });
    }));
    beforeEach(function(done) {
        zemUserService.init().then(done);
        $rootScope.$apply();
    });

    it('should correctly initialize with user data fetched from user endpoint', function() {
        expect(zemUserService.current()).toEqual(mockedUser);
        expect(zemUserService.current().id).toEqual(123);
        expect(zemUserService.current().email).toEqual('test@zemanta.com');
    });
});
