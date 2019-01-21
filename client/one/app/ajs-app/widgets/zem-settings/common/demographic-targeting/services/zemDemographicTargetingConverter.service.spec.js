describe('state: zemDemographicTargetingStateService', function() {
    var zemDemographicTargetingConverter;

    var testApiData = {
        and: [
            {or: [{category: 'bluekai: 123'}, {category: 'bluekai: 234'}]},
            {or: [{category: 'bluekai: 345'}]},
            {not: [{or: [{category: 'bluekai: 432'}]}]},
        ],
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        zemDemographicTargetingConverter = $injector.get(
            'zemDemographicTargetingConverter'
        );
    }));

    it('should convert valid inputs', function() {
        var result = zemDemographicTargetingConverter.convertFromApi(
            testApiData
        );
        expect(result).toEqual({
            type: 'and',
            parent: undefined,
            childNodes: jasmine.any(Object),
        });
    });

    it('should be reversable', function() {
        var data = zemDemographicTargetingConverter.convertFromApi(testApiData);
        var apiData = zemDemographicTargetingConverter.convertToApi(data);
        expect(apiData).toEqual(testApiData);
    });
});
