describe('state: zemDemographicTargetingStateService', function () {
    var zemDemographicTargetingConverter;

    var testApiData = {
        AND: [
            {OR: [{category: 'bluekai: 123'}, {category: 'bluekai: 234'}]},
            {OR: [{category: 'bluekai: 345'}]},
            {NOT: [{OR: [{category: 'bluekai: 432'}]}]}
        ]
    };

    beforeEach(module('one'));
    beforeEach(inject(function ($injector) {
        zemDemographicTargetingConverter = $injector.get('zemDemographicTargetingConverter');
    }));

    it('should convert valid inputs', function () {
        var result = zemDemographicTargetingConverter.convertFromApi(testApiData);
        expect(result).toEqual({type: 'and', parent: undefined, childNodes: jasmine.any(Object)});
    });

    it('should be reversable', function () {
        var data = zemDemographicTargetingConverter.convertFromApi(testApiData);
        var apiData = zemDemographicTargetingConverter.convertToApi(data);
        expect(apiData).toEqual(testApiData);
    });
});
