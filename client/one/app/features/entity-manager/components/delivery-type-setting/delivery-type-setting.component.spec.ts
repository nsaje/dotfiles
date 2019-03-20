import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DeliveryTypeSettingComponent} from './delivery-type-setting.component';

describe('DeliveryTypeSettingComponent', () => {
    let component: DeliveryTypeSettingComponent;
    let fixture: ComponentFixture<DeliveryTypeSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DeliveryTypeSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DeliveryTypeSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
