import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SelectFormGroupComponent} from './select-form-group.component';
import {SelectInputComponent} from '../select-input/select-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {NgSelectModule} from '@ng-select/ng-select';

describe('SelectFormGroupComponent', () => {
    let component: SelectFormGroupComponent;
    let fixture: ComponentFixture<SelectFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                SelectInputComponent,
                FocusDirective,
                PopoverDirective,
                HelpPopoverComponent,
                SelectFormGroupComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SelectFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
