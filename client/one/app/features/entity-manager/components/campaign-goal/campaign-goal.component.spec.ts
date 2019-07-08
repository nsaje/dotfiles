import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignGoalComponent} from './campaign-goal.component';

describe('CampaignGoalComponent', () => {
    let component: CampaignGoalComponent;
    let fixture: ComponentFixture<CampaignGoalComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignGoalComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignGoalComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
