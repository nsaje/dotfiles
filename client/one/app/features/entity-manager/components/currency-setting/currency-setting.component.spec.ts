import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CurrencySettingComponent} from './currency-setting.component';

describe('CurrencySettingComponent', () => {
    let component: CurrencySettingComponent;
    let fixture: ComponentFixture<CurrencySettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CurrencySettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CurrencySettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
