describe('zemInfoboxService', function() {
    var $injector;
    var zemInfoboxService;
    var zemInfoboxEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        zemInfoboxService = $injector.get('zemInfoboxService');
        zemInfoboxEndpoint = $injector.get('zemInfoboxEndpoint');
    }));

    it('should make a request to endpoint when reloading data if entity is not defined or null', function() {
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector
        );

        spyOn(zemInfoboxEndpoint, 'getInfoboxData').and.callFake(
            mockedAsyncFunction
        );

        zemInfoboxService.reloadInfoboxData(undefined);
        expect(zemInfoboxEndpoint.getInfoboxData).toHaveBeenCalled();

        zemInfoboxService.reloadInfoboxData(null);
        expect(zemInfoboxEndpoint.getInfoboxData).toHaveBeenCalled();
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
