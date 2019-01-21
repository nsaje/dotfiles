describe('zemInfobox', function() {
    var $injector;
    var $componentController;
    var $rootScope;
    var $httpBackend;
    var zemInfoboxService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $componentController = $injector.get('$componentController');
        $rootScope = $injector.get('$rootScope');
        $httpBackend = $injector.get('$httpBackend');
        zemInfoboxService = $injector.get('zemInfoboxService');

        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});
    }));

    it('should initialize with data from service', function() {
        var $ctrl = $componentController('zemInfobox');
        var data = {
            delivery: 'delivery',
            basicSettings: 'basicSettings',
            performanceSettings: 'performanceSettings',
        };
        var mockedAsyncFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            data
        );
        spyOn(zemInfoboxService, 'reloadInfoboxData').and.callFake(
            mockedAsyncFunction
        );

        $ctrl.$onChanges({entity: {currentValue: null}});
        $rootScope.$digest();

        expect($ctrl.delivery).toEqual(data.delivery);
        expect($ctrl.basicSettings).toEqual(data.basicSettings);
        expect($ctrl.performanceSettings).toEqual(data.performanceSettings);
    });
});
