import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignGoalEditFormComponent} from './campaign-goal-edit-form.component';
import {SelectSettingComponent} from '../select-setting/select-setting.component';
import {TextSettingComponent} from '../text-setting/text-setting.component';

describe('CampaignGoalEditFormComponent', () => {
    let component: CampaignGoalEditFormComponent;
    let fixture: ComponentFixture<CampaignGoalEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CampaignGoalEditFormComponent,
                SelectSettingComponent,
                TextSettingComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignGoalEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
