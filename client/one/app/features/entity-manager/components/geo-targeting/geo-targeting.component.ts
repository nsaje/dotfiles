import './geo-targeting.component.less';

import {
    Input,
    OnChanges,
    Output,
    EventEmitter,
    Component,
    ChangeDetectionStrategy,
    SimpleChanges,
} from '@angular/core';
import {IncludeExcludeType, GeolocationType} from '../../../../app.constants';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {GeolocationSearchParams} from '../../types/geolocation-search-params';
import {Geotargeting} from '../../types/geotargeting';
import {isEmpty} from '../../../../shared/helpers/array.helpers';
import {
    GEOLOCATION_TYPE_VALUE_TEXT,
    ITEM_LIST_LIMIT,
} from './geo-targeting.config';
import {GeolocationsByType} from '../../types/geolocations-by-type';
import * as clone from 'clone';

@Component({
    selector: 'zem-geo-targeting',
    templateUrl: './geo-targeting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoTargetingComponent implements OnChanges {
    @Input()
    includedLocationsByType: GeolocationsByType;
    @Input()
    excludedLocationsByType: GeolocationsByType;
    @Input()
    searchedLocations: Geolocation[] = [];
    @Input()
    isDisabled: boolean;
    @Input()
    isIncludedLocationSearchLoading: boolean = false;
    @Input()
    isExcludedLocationSearchLoading: boolean = false;
    @Output()
    locationSearch: EventEmitter<GeolocationSearchParams> = new EventEmitter<
        GeolocationSearchParams
    >();
    @Output()
    locationOpen: EventEmitter<void> = new EventEmitter<void>();
    @Output()
    addGeotargeting: EventEmitter<Geotargeting> = new EventEmitter<
        Geotargeting
    >();
    @Output()
    removeGeotargeting: EventEmitter<Geotargeting> = new EventEmitter<
        Geotargeting
    >();

    includedLocations: Geolocation[] = [];
    excludedLocations: Geolocation[] = [];

    isExcludedVisible: boolean = false;
    hasDifferentLocationTypes: boolean = false;
    hasNoTargeting: boolean = false;
    includedItemListLimit = {
        [GeolocationType.COUNTRY]: ITEM_LIST_LIMIT,
        [GeolocationType.REGION]: ITEM_LIST_LIMIT,
        [GeolocationType.DMA]: ITEM_LIST_LIMIT,
        [GeolocationType.CITY]: ITEM_LIST_LIMIT,
    };
    excludedItemListLimit = {
        [GeolocationType.COUNTRY]: ITEM_LIST_LIMIT,
        [GeolocationType.REGION]: ITEM_LIST_LIMIT,
        [GeolocationType.DMA]: ITEM_LIST_LIMIT,
        [GeolocationType.CITY]: ITEM_LIST_LIMIT,
    };

    geolocationTypes: GeolocationType[] = [
        GeolocationType.COUNTRY,
        GeolocationType.REGION,
        GeolocationType.DMA,
        GeolocationType.CITY,
    ];
    geolocationTypeNames = GEOLOCATION_TYPE_VALUE_TEXT;
    includeExcludeType = IncludeExcludeType;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.includedLocationsByType) {
            this.includedLocations = this.getListItems(
                this.includedLocationsByType
            );
        }
        if (changes.excludedLocationsByType) {
            this.excludedLocations = this.getListItems(
                this.excludedLocationsByType
            );
        }

        this.isExcludedVisible =
            this.isExcludedVisible || !isEmpty(this.excludedLocations);

        this.hasNoTargeting =
            isEmpty(this.includedLocations) &&
            isEmpty(this.excludedLocations) &&
            isEmpty(this.includedLocationsByType.ZIP) &&
            isEmpty(this.excludedLocationsByType.ZIP);

        this.hasDifferentLocationTypes =
            this.includedLocationsByType.COUNTRY.length > 0 &&
            (this.includedLocationsByType.CITY.length > 0 ||
                this.includedLocationsByType.REGION.length > 0 ||
                this.includedLocationsByType.DMA.length > 0);
    }

    onLocationSearch(
        nameContains: string,
        includeExcludeType: IncludeExcludeType
    ): void {
        if (nameContains.length > 1) {
            this.locationSearch.emit({
                nameContains: nameContains,
                types: this.geolocationTypes,
                limit: 10,
                offset: 0,
                target:
                    includeExcludeType === IncludeExcludeType.INCLUDE
                        ? 'include'
                        : 'exclude',
            });
        }
    }

    onAddIncludedGeotargeting(location: Geolocation): void {
        this.onShowAll(IncludeExcludeType.INCLUDE, location.type);
        this.onAddGeotargeting(location, IncludeExcludeType.INCLUDE);
    }

    onAddExcludedGeotargeting(location: Geolocation): void {
        this.onShowAll(IncludeExcludeType.EXCLUDE, location.type);
        this.onAddGeotargeting(location, IncludeExcludeType.EXCLUDE);
    }

    onAddGeotargeting(
        location: Geolocation,
        includeExcludeType: IncludeExcludeType
    ): void {
        this.addGeotargeting.emit({
            selectedLocation: location,
            includeExcludeType: includeExcludeType,
        });
    }

    onRemoveIncludedGeotargeting(location: Geolocation): void {
        this.onRemoveGeotargeting(location, IncludeExcludeType.INCLUDE);
    }

    onRemoveExcludedGeotargeting(location: Geolocation): void {
        this.onRemoveGeotargeting(location, IncludeExcludeType.EXCLUDE);
    }

    onRemoveGeotargeting(
        location: Geolocation,
        includeExcludeType: IncludeExcludeType
    ): void {
        this.removeGeotargeting.emit({
            selectedLocation: location,
            includeExcludeType: includeExcludeType,
        });
    }

    onShowAll(includeExcludeType: IncludeExcludeType, locationType: string) {
        const propertyName =
            includeExcludeType === IncludeExcludeType.INCLUDE
                ? 'includedItemListLimit'
                : 'excludedItemListLimit';
        const itemListLimit = clone(this[propertyName]);
        itemListLimit[locationType] = null;
        this[propertyName] = itemListLimit;
    }

    private getListItems(locationsByType: GeolocationsByType): Geolocation[] {
        return [].concat(
            locationsByType.COUNTRY,
            locationsByType.REGION,
            locationsByType.DMA,
            locationsByType.CITY
        );
    }
}
