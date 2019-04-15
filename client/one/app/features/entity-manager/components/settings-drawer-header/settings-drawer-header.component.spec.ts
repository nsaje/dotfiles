import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SettingsDrawerHeaderComponent} from './settings-drawer-header.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('SettingsDrawerHeaderComponent', () => {
    let component: SettingsDrawerHeaderComponent;
    let fixture: ComponentFixture<SettingsDrawerHeaderComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [SettingsDrawerHeaderComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SettingsDrawerHeaderComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
