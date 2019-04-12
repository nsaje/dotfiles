import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CheckboxSettingComponent} from './checkbox-setting.component';

describe('CheckboxSettingComponent', () => {
    let component: CheckboxSettingComponent;
    let fixture: ComponentFixture<CheckboxSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CheckboxSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CheckboxSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
