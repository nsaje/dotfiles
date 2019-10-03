import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TextFormGroupComponent} from './text-form-group.component';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {TextInputComponent} from '../text-input/text-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';

describe('TextFormGroupComponent', () => {
    let component: TextFormGroupComponent;
    let fixture: ComponentFixture<TextFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                TextInputComponent,
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                TextFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TextFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
