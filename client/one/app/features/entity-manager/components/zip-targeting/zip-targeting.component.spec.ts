import {TestBed, ComponentFixture} from '@angular/core/testing';
import {ZipTargetingComponent} from './zip-targeting.component';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {GeolocationType, IncludeExcludeType} from '../../../../app.constants';

describe('ZipTargetingComponent', () => {
    let component: ZipTargetingComponent;
    let fixture: ComponentFixture<ZipTargetingComponent>;

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

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ZipTargetingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ZipTargetingComponent);
        component = fixture.componentInstance;

        spyOn(component.targetingUpdate, 'emit').and.stub();
        spyOn(component.locationSearch, 'emit').and.stub();

        component.selectedLocation = slovenia;
        component.includeExcludeType = IncludeExcludeType.EXCLUDE;
        component.includedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: [],
        };
        component.excludedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:1000', 'SI:2000'],
        };
        component.ngOnChanges();
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly set locations, zip code text and include/exclude type', () => {
        expect(component.selectedLocation).toEqual(slovenia);
        expect(component.availableLocations).toEqual([slovenia]);
        expect(component.zipCodesText).toEqual('1000,2000');
        expect(component.includeExcludeType).toEqual(
            IncludeExcludeType.EXCLUDE
        );
    });

    it('should correctly emit update event with correct data on textarea blur event', () => {
        component.onZipCodesBlur('1000,2000');

        expect(component.targetingUpdate.emit).toHaveBeenCalledWith({
            selectedLocation: slovenia,
            includeExcludeType: IncludeExcludeType.EXCLUDE,
            zipCodes: ['SI:1000', 'SI:2000'],
        });
    });

    it('should correctly emit update event with correct data on location select event', () => {
        component.searchedLocations = [slovenia, czechia];
        component.onLocationChange(czechia.key);

        expect(component.targetingUpdate.emit).toHaveBeenCalledWith({
            selectedLocation: czechia,
            includeExcludeType: IncludeExcludeType.EXCLUDE,
            zipCodes: ['CZ:1000', 'CZ:2000'],
        });
    });

    it('should correctly emit update event with correct data on include/exclude type select event', () => {
        component.onTypeChange(IncludeExcludeType.INCLUDE);

        expect(component.targetingUpdate.emit).toHaveBeenCalledWith({
            selectedLocation: slovenia,
            includeExcludeType: IncludeExcludeType.INCLUDE,
            zipCodes: ['SI:1000', 'SI:2000'],
        });
    });

    it('should emit search event', () => {
        component.onLocationSearch('cze');
        expect(component.locationSearch.emit).toHaveBeenCalled();
    });

    it('should not emit search event (search term too short)', () => {
        component.onLocationSearch('c');
        expect(component.locationSearch.emit).not.toHaveBeenCalled();
    });

    it('should set apiOnlySettings flag when zip code country differs from each other', () => {
        component.apiOnlySettings = false;
        component.excludedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:1000', 'CZ:2000'],
        };
        component.ngOnChanges();

        expect(component.apiOnlySettings).toEqual(true);
    });

    it('should set apiOnlySettings flag to true when both included and excluded zip codes are set', () => {
        component.apiOnlySettings = false;
        component.excludedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:1000'],
        };
        component.includedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:2000'],
        };
        component.ngOnChanges();

        expect(component.apiOnlySettings).toEqual(true);
    });

    it('should set sameCountryTargeted flag to true when the same country and zip targeting country is used in included mode', () => {
        component.sameCountryTargeted = false;
        component.excludedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: [],
        };
        component.includedLocations = {
            countries: ['SI'],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:1000'],
        };
        component.includeExcludeType = IncludeExcludeType.INCLUDE;
        component.ngOnChanges();

        expect(component.sameCountryTargeted).toEqual(true);
    });

    it('should set sameCountryTargeted flag to false when the same country and zip targeting country is used in excluded mode', () => {
        component.sameCountryTargeted = true;
        component.excludedLocations = {
            countries: ['SI'],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: ['SI:1000'],
        };
        component.includedLocations = {
            countries: [],
            regions: [],
            cities: [],
            dma: [],
            postalCodes: [],
        };
        component.includeExcludeType = IncludeExcludeType.EXCLUDE;
        component.ngOnChanges();

        expect(component.sameCountryTargeted).toEqual(false);
    });
});
