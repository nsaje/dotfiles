import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AdGroupRTBSourcesManagementSettingComponent} from './ad-group-rtb-sources-management-setting.component';

describe('AdGroupRTBSourcesManagementSettingComponent', () => {
    let component: AdGroupRTBSourcesManagementSettingComponent;
    let fixture: ComponentFixture<AdGroupRTBSourcesManagementSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AdGroupRTBSourcesManagementSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            AdGroupRTBSourcesManagementSettingComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
