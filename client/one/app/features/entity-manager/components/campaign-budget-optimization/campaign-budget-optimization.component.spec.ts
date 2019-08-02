import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetOptimizationComponent} from './campaign-budget-optimization.component';

describe('CampaignBudgetOptimizationComponent', () => {
    let component: CampaignBudgetOptimizationComponent;
    let fixture: ComponentFixture<CampaignBudgetOptimizationComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignBudgetOptimizationComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignBudgetOptimizationComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
