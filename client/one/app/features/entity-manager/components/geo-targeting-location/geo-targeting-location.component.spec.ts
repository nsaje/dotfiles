import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {GeoTargetingLocationComponent} from './geo-targeting-location.component';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {GeolocationType} from '../../../../app.constants';

describe('GeoTargetingComponent', () => {
    let component: GeoTargetingLocationComponent;
    let fixture: ComponentFixture<GeoTargetingLocationComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [GeoTargetingLocationComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(GeoTargetingLocationComponent);
        component = fixture.componentInstance;
        const slovenia: Geolocation = {
            key: '754',
            type: GeolocationType.REGION,
            name: 'Mandalay Region, Myanmar [Burma]',
            outbrainId: '',
            woeid: '',
            facebookKey: '',
        };
        component.location = slovenia;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
