import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TextAreaComponent} from '../textarea/textarea.component';
import {TextAreaFormGroupComponent} from './textarea-form-group.component';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('TextAreaFormGroupComponent', () => {
    let component: TextAreaFormGroupComponent;
    let fixture: ComponentFixture<TextAreaFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                TextAreaComponent,
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                TextAreaFormGroupComponent,
                LoaderComponent,
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
