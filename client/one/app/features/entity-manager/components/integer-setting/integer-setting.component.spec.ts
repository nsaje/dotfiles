import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {IntegerSettingComponent} from './integer-setting.component';

describe('IntegerSettingComponent', () => {
    let component: IntegerSettingComponent;
    let fixture: ComponentFixture<IntegerSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [IntegerSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(IntegerSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
