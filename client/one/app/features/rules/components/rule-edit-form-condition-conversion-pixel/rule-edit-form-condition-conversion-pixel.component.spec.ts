import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormConditionConversionPixelComponent} from './rule-edit-form-condition-conversion-pixel.component';

describe('RuleEditFormConditionConversionPixelComponent', () => {
    let component: RuleEditFormConditionConversionPixelComponent;
    let fixture: ComponentFixture<RuleEditFormConditionConversionPixelComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RuleEditFormConditionConversionPixelComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            RuleEditFormConditionConversionPixelComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
