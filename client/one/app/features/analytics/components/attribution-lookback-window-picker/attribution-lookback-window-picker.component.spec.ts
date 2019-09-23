import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AttributionLoockbackWindowPickerComponent} from './attribution-lookback-window-picker.component';

describe('AttributionLoockbackWindowPickerComponent', () => {
    let component: AttributionLoockbackWindowPickerComponent;
    let fixture: ComponentFixture<AttributionLoockbackWindowPickerComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AttributionLoockbackWindowPickerComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            AttributionLoockbackWindowPickerComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
