import {IncludedExcluded} from '../../../core/entities/types/common/included-excluded';
import {TargetRegions} from '../../../core/entities/types/common/target-regions';
import * as geolocationHelpers from './geolocations.helpers';
import {GeolocationsByType} from '../types/geolocations-by-type';
import {GeolocationType} from '../../../app.constants';
import {Geolocation} from '../../../core/geolocations/types/geolocation';

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

        expect(
            geolocationHelpers.getGeolocationsKeys(mockedIncludedExcluded)
        ).toEqual(jasmine.arrayWithExactContents(keys));
    });

    it('should transform comma separated list of zip codes and country code into array of zip codes with country code', () => {
        let countryCode = 'SI';
        let zipCodes = '1000,1001,2000';
        expect(
            geolocationHelpers.getZipCodesArray(zipCodes, countryCode)
        ).toEqual(['SI:1000', 'SI:1001', 'SI:2000']);

        countryCode = 'SI';
        zipCodes = '';
        expect(
            geolocationHelpers.getZipCodesArray(zipCodes, countryCode)
        ).toEqual([]);
    });

    it('should transform zip codes with country code into comma separated list of zip codes without country code', () => {
        let zipCodesArray = ['SI:1000', 'SI:1001', 'SI:2000'];
        expect(geolocationHelpers.getZipCodesText(zipCodesArray)).toEqual(
            '1000,1001,2000'
        );

        zipCodesArray = [];
        expect(geolocationHelpers.getZipCodesText(zipCodesArray)).toEqual('');
    });

    it('should transform zip code with country code into country code', () => {
        let zipCode = 'SI:1000';
        expect(geolocationHelpers.getZipCodeCountry(zipCode)).toEqual('SI');

        zipCode = '1000';
        expect(geolocationHelpers.getZipCodeCountry(zipCode)).toEqual('1000');
    });

    it('should transform zip code with country code into zip code', () => {
        let zipCode = 'SI:1000';
        expect(geolocationHelpers.getZipCodeNumber(zipCode)).toEqual('1000');

        zipCode = 'SI';
        expect(geolocationHelpers.getZipCodeNumber(zipCode)).toEqual('');
    });

    it('should map targeting location keys to geolocations and group them by type', () => {
        const mockedTargetRegions: TargetRegions = {
            countries: ['SI'],
            regions: ['AT-2'],
            dma: ['516'],
            cities: ['217'],
            postalCodes: ['SI:1000'],
        };

        const geolocationData = {
            outbrainId: '123',
            woeid: '123',
            facebookKey: '123',
        };

        const countryLocation: Geolocation = {
            key: 'SI',
            type: GeolocationType.COUNTRY,
            name: 'Slovenia',
            ...geolocationData,
        };

        const regionLocation: Geolocation = {
            key: 'AT-2',
            type: GeolocationType.REGION,
            name: 'Lower Austria, Austria',
            ...geolocationData,
        };

        const dmaLocation: Geolocation = {
            key: '516',
            type: GeolocationType.DMA,
            name: '513 Flint-Saginaw-Bay City, MI',
            ...geolocationData,
        };

        const cityLocation: Geolocation = {
            key: '217',
            type: GeolocationType.CITY,
            name: 'Faro, Portugal',
            ...geolocationData,
        };

        const mockedSelectedLocations = [
            countryLocation,
            regionLocation,
            dmaLocation,
            cityLocation,
        ];

        const locationsByType: GeolocationsByType = {
            [GeolocationType.COUNTRY]: [countryLocation],
            [GeolocationType.REGION]: [regionLocation],
            [GeolocationType.DMA]: [dmaLocation],
            [GeolocationType.CITY]: [cityLocation],
            [GeolocationType.ZIP]: [countryLocation],
        };

        expect(
            geolocationHelpers.mapGeolocationsAndGroupByType(
                mockedTargetRegions,
                mockedSelectedLocations
            )
        ).toEqual(locationsByType);
    });
});
