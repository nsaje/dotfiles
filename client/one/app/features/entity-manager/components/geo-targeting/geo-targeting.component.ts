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
import {GeotargetingListItem} from '../../types/geotargeting-list-item';

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

    includedListItems: GeotargetingListItem[] = [];
    excludedListItems: GeotargetingListItem[] = [];
    searchedListItems: Geolocation[] = [];

    isExcludedVisible: boolean = false;
    hasDifferentLocationTypes: boolean = false;
    hasNoTargeting: boolean = false;
    expandedTypes = {
        [IncludeExcludeType.INCLUDE]: {
            [GeolocationType.COUNTRY]: false,
            [GeolocationType.REGION]: false,
            [GeolocationType.DMA]: false,
            [GeolocationType.CITY]: false,
        },
        [IncludeExcludeType.EXCLUDE]: {
            [GeolocationType.COUNTRY]: false,
            [GeolocationType.REGION]: false,
            [GeolocationType.DMA]: false,
            [GeolocationType.CITY]: false,
        },
    };

    geolocationTypes: GeolocationType[] = [
        GeolocationType.COUNTRY,
        GeolocationType.REGION,
        GeolocationType.DMA,
        GeolocationType.CITY,
    ];
    itemListLimit: number = ITEM_LIST_LIMIT;
    geolocationTypeNames = GEOLOCATION_TYPE_VALUE_TEXT;
    includeExcludeType = IncludeExcludeType;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.includedLocationsByType) {
            this.includedListItems = this.getListItems(
                this.includedLocationsByType,
                this.geolocationTypes
            );
        }
        if (changes.excludedLocationsByType) {
            this.excludedListItems = this.getListItems(
                this.excludedLocationsByType,
                this.geolocationTypes
            );
        }
        if (changes.searchedLocations) {
            this.searchedListItems = this.getSearchedListItems(
                this.searchedLocations,
                this.includedLocationsByType,
                this.excludedLocationsByType
            );
        }

        this.isExcludedVisible =
            this.isExcludedVisible || !isEmpty(this.excludedListItems);

        this.hasNoTargeting =
            isEmpty(this.includedListItems) &&
            isEmpty(this.excludedListItems) &&
            isEmpty(this.includedLocationsByType.ZIP) &&
            isEmpty(this.excludedLocationsByType.ZIP);

        this.hasDifferentLocationTypes = this.includedListItems.length > 1;
    }

    onLocationSearch(nameContains: string): void {
        if (nameContains.length > 1) {
            this.locationSearch.emit({
                nameContains: nameContains,
                types: this.geolocationTypes,
                limit: 10,
                offset: 0,
            });
        }
    }

    onAddIncludedGeotargeting(location: Geolocation): void {
        this.onAddGeotargeting(location, IncludeExcludeType.INCLUDE);
    }

    onAddExcludedGeotargeting(location: Geolocation): void {
        this.onAddGeotargeting(location, IncludeExcludeType.EXCLUDE);
    }

    onAddGeotargeting(
        location: Geolocation,
        includeExcludeType: IncludeExcludeType
    ): void {
        this.expandedTypes[includeExcludeType][location.type] = true;
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

    private getListItems(
        locationsByType: GeolocationsByType,
        geolocationTypes: GeolocationType[]
    ): GeotargetingListItem[] {
        const items: GeotargetingListItem[] = [];

        geolocationTypes.forEach(geolocationType => {
            if (!isEmpty(locationsByType[geolocationType])) {
                items.push({
                    name: GEOLOCATION_TYPE_VALUE_TEXT[geolocationType],
                    type: geolocationType,
                    locations: locationsByType[geolocationType],
                });
            }
        });
        return items;
    }

    private getSearchedListItems(
        searchedLocations: Geolocation[],
        includedLocationsByType: GeolocationsByType,
        excludedLocationsByType: GeolocationsByType
    ): Geolocation[] {
        const allSelectedLocationsKeys = []
            .concat(
                includedLocationsByType.COUNTRY,
                includedLocationsByType.REGION,
                includedLocationsByType.DMA,
                includedLocationsByType.CITY,
                excludedLocationsByType.COUNTRY,
                excludedLocationsByType.REGION,
                excludedLocationsByType.DMA,
                excludedLocationsByType.CITY
            )
            .map(location => location.key);

        return searchedLocations.filter(location => {
            return !allSelectedLocationsKeys.includes(location.key);
        });
    }
}
