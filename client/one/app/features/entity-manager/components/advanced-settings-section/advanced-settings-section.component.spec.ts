import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AdvancedSettingsSectionComponent} from './advanced-settings-section.component';

describe('AdvancedSettingsSectionComponent', () => {
    let component: AdvancedSettingsSectionComponent;
    let fixture: ComponentFixture<AdvancedSettingsSectionComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AdvancedSettingsSectionComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AdvancedSettingsSectionComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
