import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {TextSettingComponent} from './text-setting.component';

describe('TextSettingComponent', () => {
    let component: TextSettingComponent;
    let fixture: ComponentFixture<TextSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TextSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TextSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
