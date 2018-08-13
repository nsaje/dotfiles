describe('zemInfoboxService', function() {
    var $injector;
    var $rootScope;
    var zemInfoboxService;
    var zemInfoboxEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $rootScope = $injector.get('$rootScope');
        zemInfoboxService = $injector.get('zemInfoboxService');
        zemInfoboxEndpoint = $injector.get('zemInfoboxEndpoint');
    }));

    it("shouldn't make a request to endpoint when reloading data if entity is not defined", function(done) {
        var reloadPromise = zemInfoboxService.reloadInfoboxData();

        reloadPromise
            .then(function() {
                throw new Error('Promise should not be resolved');
            })
            .catch(function() {
                done();
            });

        $rootScope.$digest();
    });

    it('should make a request to endpoint when reloading data if entity is defined', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );

        spyOn(zemInfoboxEndpoint, 'getInfoboxData').and.callFake(
            mockedAsyncFunction
        );

        zemInfoboxService.reloadInfoboxData({id: 1});
        expect(zemInfoboxEndpoint.getInfoboxData).toHaveBeenCalled();
    });
});
