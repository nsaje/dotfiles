import './zip-targeting.component.less';

import {
    Component,
    Input,
    Output,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {TargetRegions} from '../../../../core/entities/types/common/target-regions';
import {IncludeExcludeType, GeolocationType} from '../../../../app.constants';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {INCLUDE_EXCLUDE_TYPES} from '../../entity-manager.config';
import {GeolocationSearchParams} from '../../types/geolocation-search-params';
import {Geotargeting} from '../../types/geotargeting';
import {isEmpty} from '../../../../shared/helpers/array.helpers';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {
    getZipCodesText,
    getZipCodesArray,
    areAllSameCountries,
} from '../../helpers/geolocations.helpers';
import * as clone from 'clone';

@Component({
    selector: 'zem-zip-targeting',
    templateUrl: './zip-targeting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ZipTargetingComponent implements OnChanges {
    @Input()
    includedLocations: TargetRegions;
    @Input()
    excludedLocations: TargetRegions;
    @Input()
    selectedLocation: Geolocation;
    @Input()
    includeExcludeType: IncludeExcludeType;
    @Input()
    searchedLocations: Geolocation[] = [];
    @Input()
    errors: string[] = [];
    @Input()
    isDisabled: boolean;
    @Output()
    locationSearch: EventEmitter<GeolocationSearchParams> = new EventEmitter<
        GeolocationSearchParams
    >();
    @Output()
    locationOpen: EventEmitter<void> = new EventEmitter<void>();
    @Output()
    targetingUpdate: EventEmitter<Geotargeting> = new EventEmitter<
        Geotargeting
    >();

    includeExcludeTypes = INCLUDE_EXCLUDE_TYPES;
    availableLocations: Geolocation[] = [];

    zipCodesText: string = '';

    sameCountryTargeted = false;
    apiOnlySettings = false;

    ngOnChanges(): void {
        this.availableLocations = this.getAvailableLocations(
            this.selectedLocation,
            this.searchedLocations
        );

        if (isEmpty(this.excludedLocations.postalCodes)) {
            this.zipCodesText = getZipCodesText(
                this.includedLocations.postalCodes
            );
        } else {
            this.zipCodesText = getZipCodesText(
                this.excludedLocations.postalCodes
            );
        }

        this.apiOnlySettings = this.getApiOnlySettings(
            this.includedLocations,
            this.excludedLocations,
            this.includeExcludeType
        );
        this.sameCountryTargeted = this.getSameCountryTargeted(
            this.includedLocations,
            this.excludedLocations,
            this.includeExcludeType,
            this.selectedLocation
        );
    }

    onLocationSearch(nameContains: string): void {
        if (nameContains.length > 1) {
            this.locationSearch.emit({
                nameContains: nameContains,
                types: [GeolocationType.COUNTRY],
                limit: 20,
                offset: 0,
            });
        }
    }

    onTypeChange(includeExcludeType: IncludeExcludeType): void {
        this.update(
            includeExcludeType,
            this.selectedLocation,
            this.zipCodesText
        );
    }

    onLocationChange(locationKey: string): void {
        const location = this.searchedLocations.find(
            searchedLocation => searchedLocation.key === locationKey
        );
        this.update(this.includeExcludeType, location, this.zipCodesText);
    }

    onZipCodesBlur(zipCodesText: string): void {
        this.update(
            this.includeExcludeType,
            this.selectedLocation,
            zipCodesText
        );
    }

    private update(
        includeExcludeType: IncludeExcludeType,
        location: Geolocation,
        zipCodesText: string
    ): void {
        if (!isDefined(location)) {
            return;
        }

        const zipCodesWithCountries = getZipCodesArray(
            zipCodesText,
            location.key
        );

        const zipTargeting: Geotargeting = {
            selectedLocation: location,
            includeExcludeType: includeExcludeType,
            zipCodes: zipCodesWithCountries,
        };

        this.targetingUpdate.emit(zipTargeting);
    }

    private getAvailableLocations(
        location: Geolocation,
        searchedLocations: Geolocation[]
    ): Geolocation[] {
        let availableLocations: Geolocation[] = [];
        if (!isEmpty(searchedLocations)) {
            availableLocations = clone(searchedLocations);
        } else if (isDefined(location)) {
            availableLocations = [location];
        }
        return availableLocations;
    }

    private getApiOnlySettings(
        includedLocations: TargetRegions,
        excludedLocations: TargetRegions,
        includeExcludeType: IncludeExcludeType
    ): boolean {
        if (
            !isEmpty(includedLocations.postalCodes) &&
            !isEmpty(excludedLocations.postalCodes)
        ) {
            return true;
        }

        const postalCodes =
            includeExcludeType === IncludeExcludeType.INCLUDE
                ? includedLocations.postalCodes
                : excludedLocations.postalCodes;

        return !areAllSameCountries(postalCodes);
    }

    private getSameCountryTargeted(
        includedLocations: TargetRegions,
        excludedLocations: TargetRegions,
        includeExcludeType: IncludeExcludeType,
        location: Geolocation
    ) {
        if (
            !isDefined(location) ||
            includeExcludeType === IncludeExcludeType.EXCLUDE
        ) {
            return false;
        }

        const targetedCountries = includedLocations.countries.concat(
            excludedLocations.countries
        );

        return targetedCountries.some(
            (countryKey: string) => countryKey === location.key
        );
    }
}
