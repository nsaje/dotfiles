describe('zemGeoTargetingStateService', function() {
    var $rootScope;
    var zemGeoTargetingStateService;
    var mockedEntity;

    beforeEach(angular.mock.module('one'));
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

        mockedEntity = {
            settings: {
                targetRegions: {
                    countries: ['a', 'b'],
                    regions: [],
                    dma: [],
                    cities: [],
                    postalCodes: [],
                },
                exclusionTargetRegions: {
                    countries: ['c', 'd'],
                    regions: [],
                    dma: [],
                    cities: [],
                    postalCodes: [],
                },
            },
        };

        var $httpBackend = $injector.get('$httpBackend');
        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});
    }));

    it('should create new state instance', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            mockedEntity
        );
        expect(stateService.getState()).toEqual({
            targetings: {
                included: [],
                excluded: [],
                notSelected: [],
            },
            messages: {
                warnings: [],
                infos: [],
            },
        });
    });

    it('should init state targetings with enabled targetings', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            mockedEntity
        );
        stateService.init();
        $rootScope.$digest();
        expect(stateService.getState().targetings.included.length).toEqual(2);
        expect(stateService.getState().targetings.excluded.length).toEqual(2);
        expect(stateService.getState().targetings.notSelected.length).toEqual(
            0
        );
        expect(stateService.getState().messages.warnings.length).toEqual(1);
        expect(stateService.getState().messages.infos.length).toEqual(1);
    });

    it('should update state targetings with enabled targetings and search results', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            mockedEntity
        );
        stateService.init();
        $rootScope.$digest();
        stateService.refresh('Location E');
        $rootScope.$digest();
        expect(stateService.getState().targetings.included.length).toEqual(2);
        expect(stateService.getState().targetings.excluded.length).toEqual(2);
        expect(stateService.getState().targetings.notSelected.length).toEqual(
            1
        );
    });

    it('should correcty add targetings', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            mockedEntity
        );
        stateService.init();
        $rootScope.$digest();
        stateService.addIncluded({id: 'inc', geolocation: {type: 'COUNTRY'}});
        stateService.addExcluded({id: 'exc', geolocation: {type: 'COUNTRY'}});
        expect(mockedEntity.settings.targetRegions.countries).toEqual([
            'a',
            'b',
            'inc',
        ]);
        expect(mockedEntity.settings.exclusionTargetRegions.countries).toEqual([
            'c',
            'd',
            'exc',
        ]);
    });

    it('should correcty remove targetings', function() {
        var stateService = zemGeoTargetingStateService.createInstance(
            mockedEntity
        );
        stateService.init();
        $rootScope.$digest();
        stateService.removeTargeting({id: 'b', geolocation: {type: 'COUNTRY'}});
        stateService.removeTargeting({id: 'd', geolocation: {type: 'COUNTRY'}});
        expect(mockedEntity.settings.targetRegions.countries).toEqual(['a']);
        expect(mockedEntity.settings.exclusionTargetRegions.countries).toEqual([
            'c',
        ]);
    });
});
