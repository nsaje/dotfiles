import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormConditionComponent} from './rule-edit-form-condition.component';
import {RuleEditFormConditionModifierComponent} from '../rule-edit-form-condition-modifier/rule-edit-form-condition-modifier.component';

describe('RuleEditFormConditionComponent', () => {
    let component: RuleEditFormConditionComponent;
    let fixture: ComponentFixture<RuleEditFormConditionComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                RuleEditFormConditionComponent,
                RuleEditFormConditionModifierComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RuleEditFormConditionComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});