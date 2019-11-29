import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AttributionColumnPickerComponent} from './attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from '../attribution-lookback-window-picker/attribution-lookback-window-picker.component';
import {PixelColumn} from '../../types/pixel-column';
import {ConversionWindow} from '../../../../app.constants';

describe('AttributionColumnPickerComponent', () => {
    let component: AttributionColumnPickerComponent;
    let fixture: ComponentFixture<AttributionColumnPickerComponent>;
    let zemPermissionsStub: any;

    beforeEach(() => {
        zemPermissionsStub = {
            hasPermission: () => '',
        };
        TestBed.configureTestingModule({
            declarations: [
                AttributionColumnPickerComponent,
                AttributionLoockbackWindowPickerComponent,
            ],
            imports: [FormsModule, SharedModule],
            providers: [
                {
                    provide: 'zemPermissions',
                    useValue: zemPermissionsStub,
                },
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AttributionColumnPickerComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
