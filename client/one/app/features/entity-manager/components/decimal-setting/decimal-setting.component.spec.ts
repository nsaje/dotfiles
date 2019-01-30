import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DecimalSettingComponent} from './decimal-setting.component';

describe('DecimalSettingComponent', () => {
    let component: DecimalSettingComponent;
    let fixture: ComponentFixture<DecimalSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DecimalSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DecimalSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
