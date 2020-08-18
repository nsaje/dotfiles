import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../../../../shared/shared.module';
import {AttributionColumnPickerComponent} from './attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from '../attribution-lookback-window-picker/attribution-lookback-window-picker.component';
import {AuthStore} from '../../../../../../../core/auth/services/auth.store';

describe('AttributionColumnPickerComponent', () => {
    let component: AttributionColumnPickerComponent;
    let fixture: ComponentFixture<AttributionColumnPickerComponent>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, ['hasPermission']);
        authStoreStub.hasPermission.and.returnValue(true);
        TestBed.configureTestingModule({
            declarations: [
                AttributionColumnPickerComponent,
                AttributionLoockbackWindowPickerComponent,
            ],
            imports: [FormsModule, SharedModule],
            providers: [
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
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
