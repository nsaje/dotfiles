import {IncludedExcluded} from '../../../core/entities/types/common/included-excluded';
import {TargetRegions} from '../../../core/entities/types/common/target-regions';
import {getGeolocationsKeys} from './geolocations.helpers';

describe('geolocationHelpers', () => {
    it('should retreive locations keys from geolocations included/excluded object', () => {
        const mockedIncludedExcluded: IncludedExcluded<TargetRegions> = {
            included: {
                countries: ['DE'],
                regions: ['AT-2'],
                dma: ['516', '423'],
                cities: ['2172517'],
                postalCodes: [],
            },
            excluded: {
                countries: [],
                regions: [],
                dma: [],
                cities: [],
                postalCodes: ['SI:1000', 'SI:2000'],
            },
        };
        const keys = ['DE', 'AT-2', '516', '423', '2172517', 'SI'];

        expect(getGeolocationsKeys(mockedIncludedExcluded)).toEqual(
            jasmine.arrayWithExactContents(keys)
        );
    });
});
