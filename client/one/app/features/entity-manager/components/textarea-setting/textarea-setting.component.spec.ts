import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TextAreaSettingComponent} from './textarea-setting.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('TextAreaSettingComponent', () => {
    let component: TextAreaSettingComponent;
    let fixture: ComponentFixture<TextAreaSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TextAreaSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TextAreaSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
