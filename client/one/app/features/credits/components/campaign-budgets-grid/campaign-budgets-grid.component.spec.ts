import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetsGridComponent} from './campaign-budgets-grid.component';

describe('CampaignBudgetsGridComponent', () => {
    let component: CampaignBudgetsGridComponent;
    let fixture: ComponentFixture<CampaignBudgetsGridComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignBudgetsGridComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignBudgetsGridComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
