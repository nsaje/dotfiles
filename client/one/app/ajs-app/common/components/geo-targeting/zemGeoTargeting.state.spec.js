describe('zemGeoTargetingStateService', function() {
    var $rootScope;
    var zemGeoTargetingStateService;
    var mockedIncludedLocations;
    var mockedExcludedLocations;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $rootScope = $injector.get('$rootScope');
        zemGeoTargetingStateService = $injector.get(
            'zemGeoTargetingStateService'
        );

        var zemGeoTargetingEndpoint = $injector.get('zemGeoTargetingEndpoint');
        var mockedMappings = [
            {
                key: 'a',
                name: 'Location A',
                type: 'COUNTRY',
                outbrainId: 'a',
                woeid: 'a',
                facebookKey: 'a',
            },
            {
                key: 'b',
                name: 'Location B',
                type: 'REGION',
                outbrainId: 'b',
                woeid: 'b',
            },
            {
                key: 'c',
                name: 'Location C',
                type: 'DMA',
                outbrainId: 'c',
                woeid: 'c',
            },
            {
                key: 'd',
                name: 'Location D',
                type: 'CITY',
                outbrainId: 'd',
                woeid: 'd',
            },
        ];
        var mockedSearch = [
            {
                key: 'a',
                name: 'Location A',
                type: 'COUNTRY',
                outbrainId: 'a',
                woeid: 'a',
                facebookKey: 'a',
            },
            {
                key: 'b',
                name: 'Location B',
                type: 'REGION',
                outbrainId: 'b',
                woeid: 'b',
            },
            {
                key: 'c',
                name: 'Location C',
                type: 'DMA',
                outbrainId: 'c',
                woeid: 'c',
            },
            {
                key: 'd',
                name: 'Location D',
                type: 'CITY',
                outbrainId: 'd',
                woeid: 'd',
            },
            {
                key: 'e',
                name: 'Location E',
                type: 'COUNTRY',
                outbrainId: 'e',
                woeid: 'e',
                facebookKey: 'e',
            },
        ];
        var mockedMapFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            mockedMappings
        );
        spyOn(zemGeoTargetingEndpoint, 'map').and.callFake(mockedMapFunction);
        var mockedSearchFunction = zemSpecsHelper.getMockedAsyncFunction(
            $injector,
            mockedSearch
        );
        spyOn(zemGeoTargetingEndpoint, 'search').and.callFake(
            mockedSearchFunction
        );

        mockedIncludedLocations = {
            countries: ['a', 'b'],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        };
        mockedExcludedLocations = {
            countries: ['c', 'd'],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        };

        var $httpBackend = $injector.get('$httpBackend');
        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});
    }));

    it('should create new state instance', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            angular.noop
        );
        expect(stateService.getState()).toEqual({
            locations: {
                included: [],
                excluded: [],
                notSelected: [],
            },
            messages: {
                warnings: [],
            },
        });
    });

    it('should init state targetings with enabled targetings', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting(
            mockedIncludedLocations,
            mockedExcludedLocations
        );
        $rootScope.$digest();
        expect(stateService.getState().locations.included.length).toEqual(2);
        expect(stateService.getState().locations.excluded.length).toEqual(2);
        expect(stateService.getState().locations.notSelected.length).toEqual(0);
        expect(stateService.getState().messages.warnings.length).toEqual(1);
    });

    it('should update state targetings with enabled targetings and search results', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting(
            mockedIncludedLocations,
            mockedExcludedLocations
        );
        $rootScope.$digest();
        stateService.refresh('Location E');
        $rootScope.$digest();
        expect(stateService.getState().locations.included.length).toEqual(2);
        expect(stateService.getState().locations.excluded.length).toEqual(2);
        expect(stateService.getState().locations.notSelected.length).toEqual(1);
    });

    it('should correctly add targetings', function() {
        var spy = jasmine.createSpy('spy');
        var stateService = zemGeoTargetingStateService.createInstance(spy);
        stateService.updateTargeting(
            mockedIncludedLocations,
            mockedExcludedLocations
        );
        $rootScope.$digest();
        stateService.addIncluded({id: 'inc', geolocation: {type: 'COUNTRY'}});
        expect(spy.calls.argsFor(0)[0].includedLocations.countries).toEqual([
            'a',
            'b',
            'inc',
        ]);
        stateService.addExcluded({id: 'exc', geolocation: {type: 'COUNTRY'}});
        expect(spy.calls.argsFor(1)[0].excludedLocations.countries).toEqual([
            'c',
            'd',
            'exc',
        ]);
    });

    it('should correctly remove targetings', function() {
        var spy = jasmine.createSpy('spy');
        var stateService = zemGeoTargetingStateService.createInstance(spy);
        stateService.updateTargeting(
            mockedIncludedLocations,
            mockedExcludedLocations
        );
        $rootScope.$digest();
        stateService.removeLocation({id: 'b', geolocation: {type: 'COUNTRY'}});
        stateService.removeLocation({id: 'd', geolocation: {type: 'COUNTRY'}});

        expect(spy.calls.argsFor(0)[0].includedLocations.countries).toEqual([
            'a',
        ]);
        expect(spy.calls.argsFor(1)[0].excludedLocations.countries).toEqual([
            'c',
        ]);
    });
});
