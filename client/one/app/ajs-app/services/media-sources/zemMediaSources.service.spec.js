describe('zemMediaSourcesService', function() {
    var $rootScope;
    var zemMediaSourcesService;
    var zemMediaSourcesEndpoint;
    var mockedSources = [
        {
            id: 1,
            name: 'Media source 1',
            deprecated: false,
        },
        {
            id: 2,
            name: 'Media source 2',
            deprecated: true,
        },
    ];

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        _$rootScope_,
        $q,
        _zemMediaSourcesService_,
        _zemMediaSourcesEndpoint_
    ) {
        // eslint-disable-line max-len
        $rootScope = _$rootScope_;
        zemMediaSourcesService = _zemMediaSourcesService_;
        zemMediaSourcesEndpoint = _zemMediaSourcesEndpoint_;

        spyOn(zemMediaSourcesEndpoint, 'getSources').and.callFake(function() {
            var deferred = $q.defer();
            var response = {data: {sources: mockedSources}};
            deferred.resolve(response);
            return deferred.promise;
        });

        zemMediaSourcesService.init();
        $rootScope.$apply();
    }));

    it('should correctly return sources fetched from backend', function(done) {
        zemMediaSourcesService.getSources().then(function(sources) {
            expect(zemMediaSourcesEndpoint.getSources).toHaveBeenCalled();
            expect(sources.length).toEqual(2);
            done();
        });
        $rootScope.$apply();
    });

    it('should return cached sources if sources were already fetched from backend', function(done) {
        zemMediaSourcesService.getSources().then(function() {
            zemMediaSourcesService.getSources().then(function(sources) {
                expect(
                    zemMediaSourcesEndpoint.getSources.calls.count()
                ).toEqual(1);
                expect(sources.length).toEqual(2);
                done();
            });
        });
        $rootScope.$apply();
    });

    it('should corectly force refetch sources', function(done) {
        zemMediaSourcesService.getSources().then(function() {
            zemMediaSourcesService.getSources(true).then(function(sources) {
                expect(
                    zemMediaSourcesEndpoint.getSources.calls.count()
                ).toEqual(2);
                expect(sources.length).toEqual(2);
                done();
            });
        });
        $rootScope.$apply();
    });

    it('should correctly return available sources fetched from backend', function(done) {
        zemMediaSourcesService.getAvailableSources().then(function(sources) {
            expect(zemMediaSourcesEndpoint.getSources).toHaveBeenCalled();
            expect(sources.length).toEqual(1);
            done();
        });
        $rootScope.$apply();
    });

    it('should return cached available sources if sources were already fetched from backend', function(done) {
        zemMediaSourcesService.getAvailableSources().then(function() {
            zemMediaSourcesService
                .getAvailableSources()
                .then(function(sources) {
                    expect(
                        zemMediaSourcesEndpoint.getSources.calls.count()
                    ).toEqual(1);
                    expect(sources.length).toEqual(1);
                    done();
                });
        });
        $rootScope.$apply();
    });

    it('should corectly force refetch sources and return available sources', function(done) {
        zemMediaSourcesService.getAvailableSources().then(function() {
            zemMediaSourcesService
                .getAvailableSources(true)
                .then(function(sources) {
                    expect(
                        zemMediaSourcesEndpoint.getSources.calls.count()
                    ).toEqual(2);
                    expect(sources.length).toEqual(1);
                    done();
                });
        });
        $rootScope.$apply();
    });
});
