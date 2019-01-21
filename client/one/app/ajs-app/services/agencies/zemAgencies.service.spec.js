describe('zemAgenciesService', function() {
    var $rootScope;
    var zemAgenciesService;
    var zemAgenciesEndpoint;
    var mockedAgencies = [
        {
            id: 1,
            name: 'Agency 1',
        },
        {
            id: 2,
            name: 'Agency 2',
        },
    ];

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        _$rootScope_,
        $q,
        _zemAgenciesService_,
        _zemAgenciesEndpoint_
    ) {
        $rootScope = _$rootScope_;
        zemAgenciesService = _zemAgenciesService_;
        zemAgenciesEndpoint = _zemAgenciesEndpoint_;

        spyOn(zemAgenciesEndpoint, 'getAgencies').and.callFake(function() {
            var deferred = $q.defer();
            var response = {data: {agencies: mockedAgencies}};
            deferred.resolve(response);
            return deferred.promise;
        });
    }));

    it('should correctly return agencies fetched from backend', function(done) {
        zemAgenciesService
            .getAgencies()
            .then(function(agencies) {
                expect(zemAgenciesEndpoint.getAgencies).toHaveBeenCalled();
                expect(agencies.length).toEqual(2);
                done();
            })
            .catch(done.fail);
        $rootScope.$apply();
    });

    it('should return cached agencies if agencies were already fetched from backend', function(done) {
        zemAgenciesService
            .getAgencies()
            .then(function() {
                zemAgenciesService
                    .getAgencies()
                    .then(function(agencies) {
                        expect(
                            zemAgenciesEndpoint.getAgencies.calls.count()
                        ).toEqual(1);
                        expect(agencies.length).toEqual(2);
                        done();
                    })
                    .catch(done.fail);
            })
            .catch(done.fail);
        $rootScope.$apply();
    });

    it('should corectly force refetch agencies', function(done) {
        zemAgenciesService
            .getAgencies()
            .then(function() {
                zemAgenciesService
                    .getAgencies(true)
                    .then(function(agencies) {
                        expect(
                            zemAgenciesEndpoint.getAgencies.calls.count()
                        ).toEqual(2);
                        expect(agencies.length).toEqual(2);
                        done();
                    })
                    .catch(done.fail);
            })
            .catch(done.fail);
        $rootScope.$apply();
    });
});
