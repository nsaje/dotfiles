import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DailyBudgetSettingComponent} from './daily-budget-setting.component';

describe('DailyBudgetSettingComponent', () => {
    let component: DailyBudgetSettingComponent;
    let fixture: ComponentFixture<DailyBudgetSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DailyBudgetSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DailyBudgetSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
