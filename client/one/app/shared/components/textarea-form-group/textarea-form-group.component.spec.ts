import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TextAreaFormGroupComponent} from './textarea-form-group.component';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {FocusDirective} from '../../directives/focus/focus.directive';

describe('TextAreaFormGroupComponent', () => {
    let component: TextAreaFormGroupComponent;
    let fixture: ComponentFixture<TextAreaFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                TextAreaFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TextAreaFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
