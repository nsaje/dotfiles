import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TrackingCodeSettingComponent} from './tracking-code-setting.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('TrackingCodeSettingComponent', () => {
    let component: TrackingCodeSettingComponent;
    let fixture: ComponentFixture<TrackingCodeSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TrackingCodeSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TrackingCodeSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
