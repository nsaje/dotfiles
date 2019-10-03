import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {CurrencyFormGroupComponent} from './currency-form-group.component';
import {CurrencyInputComponent} from '../currency-input/currency-input.component';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {PrefixedInputComponent} from '../prefixed-input/prefixed-input.component';
import {PopoverDirective} from '../popover/popover.directive';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event/filter-keydown-event.directive';
import {FocusDirective} from '../../directives/focus/focus.directive';

describe('CurrencyFormGroupComponent', () => {
    let component: CurrencyFormGroupComponent;
    let fixture: ComponentFixture<CurrencyFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                PrefixedInputComponent,
                CurrencyInputComponent,
                HelpPopoverComponent,
                PopoverDirective,
                FilterKeydownEventDirective,
                FocusDirective,
                CurrencyFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CurrencyFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
