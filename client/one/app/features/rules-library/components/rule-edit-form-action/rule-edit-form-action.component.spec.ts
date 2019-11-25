import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormActionComponent} from './rule-edit-form-action.component';

describe('RuleEditFormActionComponent', () => {
    let component: RuleEditFormActionComponent;
    let fixture: ComponentFixture<RuleEditFormActionComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RuleEditFormActionComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RuleEditFormActionComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
