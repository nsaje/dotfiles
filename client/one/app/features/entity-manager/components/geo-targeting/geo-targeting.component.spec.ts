import {TestBed, ComponentFixture} from '@angular/core/testing';
import {GeoTargetingComponent} from './geo-targeting.component';
import {GeoTargetingLocationComponent} from '../geo-targeting-location/geo-targeting-location.component';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {GeolocationType, IncludeExcludeType} from '../../../../app.constants';
import {GEOLOCATION_TYPE_VALUE_TEXT} from './geo-targeting.config';
import {SimpleChange} from '@angular/core';
import {GeolocationsByType} from '../../types/geolocations-by-type';

describe('GeoTargetingComponent', () => {
    let component: GeoTargetingComponent;
    let fixture: ComponentFixture<GeoTargetingComponent>;

    const slovenia: Geolocation = {
        key: 'SI',
        type: GeolocationType.COUNTRY,
        name: 'Slovenia',
        outbrainId: 'dafd9b2285eb829458b9982a9ff8792b',
        woeid: '23424748',
        facebookKey: 'SI',
    };
    const czechia: Geolocation = {
        key: 'CZ',
        type: GeolocationType.COUNTRY,
        name: 'Czechia',
        outbrainId: 'dafd9b2285eb829458b9982a9ff8792b',
        woeid: '23424748',
        facebookKey: 'CZ',
    };
    const austria: Geolocation = {
        key: 'AT',
        type: GeolocationType.COUNTRY,
        name: 'Austria',
        outbrainId: 'dafd9b2285eb829458b9982a9ff8792b',
        woeid: '23424748',
        facebookKey: 'AT',
    };
    const austriaRegion: Geolocation = {
        key: 'AT-2',
        type: GeolocationType.REGION,
        name: 'Lower Austria, Austria',
        outbrainId: 'dafd9b2285eb829458b9982a9ff8792b',
        woeid: '23424748',
        facebookKey: 'AT-2',
    };

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                GeoTargetingComponent,
                GeoTargetingLocationComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(GeoTargetingComponent);
        component = fixture.componentInstance;

        spyOn(component.addGeotargeting, 'emit').and.stub();
        spyOn(component.removeGeotargeting, 'emit').and.stub();
        spyOn(component.locationSearch, 'emit').and.stub();

        const locationsByType: GeolocationsByType = {
            [GeolocationType.COUNTRY]: [],
            [GeolocationType.REGION]: [],
            [GeolocationType.DMA]: [],
            [GeolocationType.CITY]: [],
            [GeolocationType.ZIP]: [],
        };

        component.includedLocationsByType = locationsByType;
        component.excludedLocationsByType = locationsByType;

        component.ngOnChanges({
            includedLocationsByType: new SimpleChange(
                null,
                locationsByType,
                false
            ),
            excludedLocationsByType: new SimpleChange(
                null,
                locationsByType,
                false
            ),
        });
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should has no targeting flag set when no locations are selected', () => {
        expect(component.hasNoTargeting).toEqual(true);
    });

    it('shoud emit add geotargeting event with correct data on location add event', () => {
        component.onAddIncludedGeotargeting(slovenia);
        expect(component.addGeotargeting.emit).toHaveBeenCalledWith({
            selectedLocation: slovenia,
            includeExcludeType: IncludeExcludeType.INCLUDE,
        });

        component.onAddExcludedGeotargeting(czechia);
        expect(component.addGeotargeting.emit).toHaveBeenCalledWith({
            selectedLocation: czechia,
            includeExcludeType: IncludeExcludeType.EXCLUDE,
        });
    });

    it('shoud emit remove geotargeting event with correct data on location remove event', () => {
        component.onRemoveIncludedGeotargeting(slovenia);
        expect(component.removeGeotargeting.emit).toHaveBeenCalledWith({
            selectedLocation: slovenia,
            includeExcludeType: IncludeExcludeType.INCLUDE,
        });

        component.onRemoveExcludedGeotargeting(czechia);
        expect(component.removeGeotargeting.emit).toHaveBeenCalledWith({
            selectedLocation: czechia,
            includeExcludeType: IncludeExcludeType.EXCLUDE,
        });
    });

    it('should emit search event', () => {
        component.onLocationSearch('cze', IncludeExcludeType.INCLUDE);
        expect(component.locationSearch.emit).toHaveBeenCalled();
    });

    it('should not emit search event (search term too short)', () => {
        component.onLocationSearch('c', IncludeExcludeType.INCLUDE);
        expect(component.locationSearch.emit).not.toHaveBeenCalled();
    });

    it('should transform locations by type into array of geolocations and set has different included location type flag', () => {
        const locationsByType: GeolocationsByType = {
            [GeolocationType.COUNTRY]: [slovenia, czechia],
            [GeolocationType.REGION]: [austriaRegion],
            [GeolocationType.DMA]: [],
            [GeolocationType.CITY]: [],
            [GeolocationType.ZIP]: [],
        };
        component.includedLocationsByType = locationsByType;

        component.ngOnChanges({
            includedLocationsByType: new SimpleChange(
                null,
                locationsByType,
                false
            ),
        });

        expect(component.includedLocations).toEqual([
            slovenia,
            czechia,
            austriaRegion,
        ]);
        expect(component.hasDifferentLocationTypes).toEqual(true);
    });

    it('should correctly set excluded visible flag', () => {
        const locationsByType: GeolocationsByType = {
            [GeolocationType.COUNTRY]: [slovenia, czechia],
            [GeolocationType.REGION]: [austriaRegion],
            [GeolocationType.DMA]: [],
            [GeolocationType.CITY]: [],
            [GeolocationType.ZIP]: [],
        };
        component.excludedLocationsByType = locationsByType;

        component.ngOnChanges({
            excludedLocationsByType: new SimpleChange(
                null,
                locationsByType,
                false
            ),
        });

        expect(component.isExcludedVisible).toEqual(true);
    });
});
