describe('zemZipTargetingStateService', function() {
    var zemZipTargetingStateService;
    var mockedEntity;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector, $q) {
        zemZipTargetingStateService = $injector.get(
            'zemZipTargetingStateService'
        );

        var zemGeoTargetingEndpoint = $injector.get('zemGeoTargetingEndpoint');
        var mockedMapFunction = function(key) {
            var deferred = $q.defer();
            var loc = {
                key: key,
                name: 'Location A',
                type: 'COUNTRY',
                outbrainId: 'a',
                woeid: 'a',
                facebookKey: 'a',
            };
            deferred.resolve(loc);
            return deferred.promise;
        };
        spyOn(zemGeoTargetingEndpoint, 'mapKey').and.callFake(
            mockedMapFunction
        );

        mockedEntity = {
            settings: {
                targetRegions: ['a', 'b'],
                exclusionTargetRegions: ['c', 'd'],
            },
        };

        var $httpBackend = $injector.get('$httpBackend');
        $httpBackend.whenGET(/^\/api\/.*/).respond(200, {data: {}});
    }));

    it('should create new state instance', function() {
        var stateService = zemZipTargetingStateService.createInstance(
            mockedEntity
        );
        expect(stateService.getState()).toEqual({
            zipTargetingType: '',
            selectedCountry: '',
            textareaContent: '',
            countrySearchResults: [],
            blockers: {
                apiOnlySettings: false,
                countryIncluded: false,
            },
        });
    });

    it('should init country correctly', function() {
        var stateService = zemZipTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting({}, {});
        expect(stateService.getState().selectedCountry.key).toEqual('US');

        stateService.updateTargeting(
            {postalCodes: ['SI:1', 'US:2']},
            {postalCodes: []}
        );
        expect(stateService.getState().selectedCountry.key).toEqual('SI');
    });

    it('should init textarea correctly', function() {
        var stateService = zemZipTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting({}, {});
        expect(stateService.getState().textareaContent).toEqual('');

        stateService.updateTargeting(
            {postalCodes: ['US:1', 'US:2']},
            {postalCodes: []}
        );
        expect(stateService.getState().textareaContent).toEqual('1, 2');
    });

    it('should init api only correctly', function() {
        var stateService = zemZipTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting(
            {postalCodes: ['US:1', 'SI:1']},
            {postalCodes: []}
        );
        expect(stateService.getState().blockers.apiOnlySettings).toEqual(true);

        stateService.updateTargeting(
            {postalCodes: ['US:1']},
            {postalCodes: ['US:2']}
        );
        expect(stateService.getState().blockers.apiOnlySettings).toEqual(true);
    });

    it('should detect country is included in general targeting', function() {
        var stateService = zemZipTargetingStateService.createInstance(
            angular.noop
        );
        stateService.updateTargeting(
            {
                countries: ['US'],
                postalCodes: ['US:1'],
            },
            {postalCodes: []}
        );
        expect(stateService.getState().blockers.countryIncluded).toEqual(true);
    });
});
