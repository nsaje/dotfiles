import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormConditionsComponent} from './rule-edit-form-conditions.component';
import {RuleEditFormConditionComponent} from '../rule-edit-form-condition/rule-edit-form-condition.component';
import {RuleEditFormConditionModifierComponent} from '../rule-edit-form-condition-modifier/rule-edit-form-condition-modifier.component';

describe('RuleEditFormConditionsComponent', () => {
    let component: RuleEditFormConditionsComponent;
    let fixture: ComponentFixture<RuleEditFormConditionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                RuleEditFormConditionsComponent,
                RuleEditFormConditionComponent,
                RuleEditFormConditionModifierComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RuleEditFormConditionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
