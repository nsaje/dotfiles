import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {IntegerFormGroupComponent} from './integer-form-group.component';
import {IntegerInputComponent} from '../integer-input/integer-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event/filter-keydown-event.directive';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';

describe('IntegerFormGroupComponent', () => {
    let component: IntegerFormGroupComponent;
    let fixture: ComponentFixture<IntegerFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                IntegerInputComponent,
                FilterKeydownEventDirective,
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                IntegerFormGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(IntegerFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
