import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SimpleChange} from '@angular/core';
import {DateFormGroupComponent} from './date-form-group.component';
import {PopoverDirective} from '../popover/popover.directive';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';
import {DateInputComponent} from '../date-input/date-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';

describe('DateFormGroupComponent', () => {
    let component: DateFormGroupComponent;
    let fixture: ComponentFixture<DateFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CheckboxInputComponent,
                HelpPopoverComponent,
                PopoverDirective,
                DateInputComponent,
                FocusDirective,
                DateFormGroupComponent,
            ],
            imports: [FormsModule, NgbDatepickerModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DateFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized when value input is defined', () => {
        const mockedDate = new Date();
        component.value = mockedDate;
        component.ngOnChanges({
            value: new SimpleChange(null, mockedDate, false),
        });
        expect(component.model).toEqual(mockedDate);
        expect(component.lastNonNullValue).toEqual(mockedDate);
        expect(component.isManualOverrideEnabled).toBe(false);
    });

    it('should be correctly initialized when value input is not defined', () => {
        const mockedDate: Date = null;
        component.value = mockedDate;
        component.ngOnChanges({
            value: new SimpleChange(null, mockedDate, false),
        });
        expect(component.model).toEqual(null);
        expect(component.lastNonNullValue).toBe(undefined);
        expect(component.isManualOverrideEnabled).toBe(false);
    });

    it('should emit null in valueChange output when manual override is toggled on', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.onManualOverrideToggle(true);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
    });

    it('should emit last selected date in valueChange output when manual override is toggled off', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        const mockedDate = new Date();
        component.lastNonNullValue = mockedDate;
        component.onManualOverrideToggle(false);
        expect(component.valueChange.emit).toHaveBeenCalledWith(mockedDate);
    });

    it('should emit min date in valueChange output when manual override is toggled off and last selected date is not available', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        const mockedDate = new Date();
        component.minDate = mockedDate;
        component.onManualOverrideToggle(false);
        expect(component.valueChange.emit).toHaveBeenCalledWith(mockedDate);
    });
});
