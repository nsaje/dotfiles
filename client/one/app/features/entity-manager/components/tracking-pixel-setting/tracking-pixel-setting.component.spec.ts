import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TrackingPixelSettingComponent} from './tracking-pixel-setting.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('TrackingCodeSettingComponent', () => {
    let component: TrackingPixelSettingComponent;
    let fixture: ComponentFixture<TrackingPixelSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TrackingPixelSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TrackingPixelSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
