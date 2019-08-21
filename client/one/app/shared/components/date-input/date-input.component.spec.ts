import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {NgbDatepickerModule, NgbDate} from '@ng-bootstrap/ng-bootstrap';
import {DateInputComponent} from './date-input.component';
import {SimpleChange} from '@angular/core';
import {FocusDirective} from '../../directives/focus/focus.directive';

describe('DateInputComponent', () => {
    let component: DateInputComponent;
    let fixture: ComponentFixture<DateInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DateInputComponent, FocusDirective],
            imports: [FormsModule, NgbDatepickerModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DateInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly format model on changes', () => {
        const value = new Date(2019, 0, 5);
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual(new NgbDate(2019, 1, 5));
    });

    it('should correctly format model on onDateSelect event', () => {
        spyOn(component.valueChange, 'emit').and.stub();

        component.onDateSelect(new NgbDate(2019, 1, 5));
        expect(component.valueChange.emit).toHaveBeenCalledWith(
            new Date(2019, 0, 5)
        );
    });

    it('should correctly format minDate on changes', () => {
        const originalMinDate = new Date(2019, 0, 5);
        component.originalMinDate = originalMinDate;
        component.ngOnChanges({
            originalMinDate: new SimpleChange(null, originalMinDate, false),
        });
        expect(component.minDate).toEqual(new NgbDate(2019, 1, 5));
    });

    it('should correctly format maxDate on changes', () => {
        const originalMaxDate = new Date(2019, 0, 5);
        component.originalMaxDate = originalMaxDate;
        component.ngOnChanges({
            originalMaxDate: new SimpleChange(null, originalMaxDate, false),
        });
        expect(component.maxDate).toEqual(new NgbDate(2019, 1, 5));
    });
});
