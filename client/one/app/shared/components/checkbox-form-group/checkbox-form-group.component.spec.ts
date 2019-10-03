import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {CheckboxFormGroupComponent} from './checkbox-form-group.component';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {PopoverDirective} from '../popover/popover.directive';

describe('CheckboxFormGroupComponent', () => {
    let component: CheckboxFormGroupComponent;
    let fixture: ComponentFixture<CheckboxFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CheckboxInputComponent,
                HelpPopoverComponent,
                PopoverDirective,
                CheckboxFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CheckboxFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
