import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DateSettingComponent} from './date-setting.component';

describe('DateSettingComponent', () => {
    let component: DateSettingComponent;
    let fixture: ComponentFixture<DateSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DateSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DateSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
