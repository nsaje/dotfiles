import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormConditionModifierComponent} from './rule-edit-form-condition-modifier.component';

describe('RuleEditFormConditionModifierComponent', () => {
    let component: RuleEditFormConditionModifierComponent;
    let fixture: ComponentFixture<RuleEditFormConditionModifierComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RuleEditFormConditionModifierComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            RuleEditFormConditionModifierComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
