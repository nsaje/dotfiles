import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignGoalsComponent} from './campaign-goals.component';
import {CampaignGoalComponent} from '../campaign-goal/campaign-goal.component';
import {CampaignGoalEditFormComponent} from '../campaign-goal-edit-form/campaign-goal-edit-form.component';

describe('CampaignGoalsComponent', () => {
    let component: CampaignGoalsComponent;
    let fixture: ComponentFixture<CampaignGoalsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CampaignGoalsComponent,
                CampaignGoalComponent,
                CampaignGoalEditFormComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignGoalsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
