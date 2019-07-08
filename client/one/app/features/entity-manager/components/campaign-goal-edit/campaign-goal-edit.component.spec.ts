import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignGoalEditComponent} from './campaign-goal-edit.component';
import {SelectSettingComponent} from '../select-setting/select-setting.component';
import {TextSettingComponent} from '../text-setting/text-setting.component';

describe('CampaignGoalEditComponent', () => {
    let component: CampaignGoalEditComponent;
    let fixture: ComponentFixture<CampaignGoalEditComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CampaignGoalEditComponent,
                SelectSettingComponent,
                TextSettingComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignGoalEditComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
