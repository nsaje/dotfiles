import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {DecimalFormGroupComponent} from './decimal-form-group.component';
import {PrefixedInputComponent} from '../prefixed-input/prefixed-input.component';
import {DecimalInputComponent} from '../decimal-input/decimal-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event/filter-keydown-event.directive';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';

describe('DecimalFormGroupComponent', () => {
    let component: DecimalFormGroupComponent;
    let fixture: ComponentFixture<DecimalFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                PrefixedInputComponent,
                DecimalInputComponent,
                FilterKeydownEventDirective,
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                DecimalFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DecimalFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
