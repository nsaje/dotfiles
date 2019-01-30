import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {SelectSettingComponent} from './select-setting.component';

describe('SelectSettingComponent', () => {
    let component: SelectSettingComponent;
    let fixture: ComponentFixture<SelectSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [SelectSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SelectSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
