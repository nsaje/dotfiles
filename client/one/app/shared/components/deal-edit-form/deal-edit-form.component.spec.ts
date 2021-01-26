import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {DealEditFormComponent} from './deal-edit-form.component';
import {TextInputComponent} from '../text-input/text-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {TextFormGroupComponent} from '../text-form-group/text-form-group.component';
import {TextAreaComponent} from '../textarea/textarea.component';
import {TextAreaFormGroupComponent} from '../textarea-form-group/textarea-form-group.component';
import {SelectFormGroupComponent} from '../select-form-group/select-form-group.component';
import {SelectInputComponent} from '../select-input/select-input.component';
import {DateFormGroupComponent} from '../date-form-group/date-form-group.component';
import {DateInputComponent} from '../date-input/date-input.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';
import {DecimalInputComponent} from '../decimal-input/decimal-input.component';
import {DecimalFormGroupComponent} from '../decimal-form-group/decimal-form-group.component';
import {PrefixedInputComponent} from '../prefixed-input/prefixed-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event/filter-keydown-event.directive';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('DealEditFormComponent', () => {
    let component: DealEditFormComponent;
    let fixture: ComponentFixture<DealEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                FocusDirective,
                PopoverDirective,
                FilterKeydownEventDirective,
                TextHighlightDirective,
                HelpPopoverComponent,
                CheckboxInputComponent,
                PrefixedInputComponent,
                TextInputComponent,
                DecimalInputComponent,
                SelectInputComponent,
                DateInputComponent,
                TextFormGroupComponent,
                TextAreaComponent,
                TextAreaFormGroupComponent,
                DecimalFormGroupComponent,
                SelectFormGroupComponent,
                DateFormGroupComponent,
                DealEditFormComponent,
                LoaderComponent,
            ],
            imports: [FormsModule, NgSelectModule, NgbDatepickerModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
