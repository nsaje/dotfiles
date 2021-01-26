import {IncludedExcluded} from '../../../core/entities/types/common/included-excluded';
import {TargetRegions} from '../../../core/entities/types/common/target-regions';
import {GeolocationType, IncludeExcludeType} from '../../../app.constants';
import {isEmpty} from '../../../shared/helpers/array.helpers';
import {getValueOrDefault} from '../../../shared/helpers/common.helpers';
import {Geolocation} from '../../../core/geolocations/types/geolocation';
import {GeolocationsByType} from '../types/geolocations-by-type';

export function getGeolocationsKeys(
    geotargeting: IncludedExcluded<TargetRegions>
): string[] {
    let keys: string[] = [];
    Object.keys(geotargeting).forEach((geotargetingType: string) => {
        keys = keys.concat(
            ...geotargeting[geotargetingType].countries,
            ...geotargeting[geotargetingType].regions,
            ...geotargeting[geotargetingType].dma,
            ...geotargeting[geotargetingType].cities,
            geotargeting[geotargetingType].postalCodes.length
                ? [geotargeting[geotargetingType].postalCodes[0].split(':')[0]]
                : []
        );
    });
    return keys;
}

export function getGeotargetingLocationPropertyFromGeolocationType(
    geolocationType: GeolocationType
): string {
    if (geolocationType === GeolocationType.COUNTRY) {
        return 'countries';
    } else if (geolocationType === GeolocationType.REGION) {
        return 'regions';
    } else if (geolocationType === GeolocationType.DMA) {
        return 'dma';
    } else if (geolocationType === GeolocationType.CITY) {
        return 'cities';
    } else if (geolocationType === GeolocationType.ZIP) {
        return 'postalCodes';
    }
}

export function getIncludeExcludePropertyNameFromIncludeExcludeType(
    includeExcludeType: IncludeExcludeType
): string {
    return includeExcludeType === IncludeExcludeType.INCLUDE
        ? 'included'
        : 'excluded';
}

export function getZipCodeCountry(zipCode: string): string {
    return zipCode.split(':')[0];
}

export function getZipCodeNumber(zipCode: string): string {
    const parts = zipCode.split(':');
    return getValueOrDefault(parts[1], '');
}

export function getZipCodesArray(
    zipCodesText: string,
    countryCode: string
): string[] {
    return zipCodesText
        .trim()
        .split(/\s*[,\n]+\s*/)
        .filter(zip => zip)
        .map((zipCode: string) => {
            return `${countryCode}:${zipCode}`;
        });
}

export function getZipCodesText(zipCodesArray: string[]): string {
    return zipCodesArray.map(zipCode => getZipCodeNumber(zipCode)).join(',');
}

export function areAllSameCountries(zipCodes: string[]): boolean {
    if (isEmpty(zipCodes)) {
        return true;
    }

    const zipCodeFirstCountry = getZipCodeCountry(zipCodes[0]);
    return zipCodes.every(
        (zipCode: string) => getZipCodeCountry(zipCode) === zipCodeFirstCountry
    );
}

export function mapGeolocationsAndGroupByType(
    geolocationTargeting: TargetRegions,
    geolocations: Geolocation[]
): GeolocationsByType {
    const geolocationsByType: GeolocationsByType = {
        [GeolocationType.COUNTRY]: [],
        [GeolocationType.REGION]: [],
        [GeolocationType.DMA]: [],
        [GeolocationType.CITY]: [],
        [GeolocationType.ZIP]: [],
    };

    [
        GeolocationType.COUNTRY,
        GeolocationType.REGION,
        GeolocationType.DMA,
        GeolocationType.CITY,
    ].forEach(geolocationType => {
        const geolocationPropertyName = getGeotargetingLocationPropertyFromGeolocationType(
            geolocationType
        );
        geolocationsByType[geolocationType] = geolocationTargeting[
            geolocationPropertyName
        ].map((geolocationKey: string) => {
            const geolocation = geolocations.find(
                geolocation => geolocation.key === geolocationKey
            );
            return geolocation;
        });
    });

    if (!isEmpty(geolocationTargeting.postalCodes)) {
        geolocationsByType.ZIP = [
            geolocations.find(
                geolocation =>
                    geolocation.key ===
                    getZipCodeCountry(geolocationTargeting.postalCodes[0])
            ),
        ];
    }
    return geolocationsByType;
}
