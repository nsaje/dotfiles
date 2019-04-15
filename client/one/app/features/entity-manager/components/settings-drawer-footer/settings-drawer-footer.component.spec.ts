import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SettingsDrawerFooterComponent} from './settings-drawer-footer.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('SettingsDrawerFooterComponent', () => {
    let component: SettingsDrawerFooterComponent;
    let fixture: ComponentFixture<SettingsDrawerFooterComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [SettingsDrawerFooterComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SettingsDrawerFooterComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
