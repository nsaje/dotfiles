import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {NgbDatepickerModule, NgbDate} from '@ng-bootstrap/ng-bootstrap';
import {DateInputComponent} from './date-input.component';
import {SimpleChange} from '@angular/core';
import {FocusDirective} from '../../directives/focus.directive';

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
        component.ngOnInit();
        expect(component).toBeDefined();
    });

    it('should correctly initialize minDate', () => {
        component.originalMinDate = new Date(2019, 0, 5);
        component.ngOnInit();
        expect(component.minDate).toEqual(new NgbDate(2019, 1, 5));
    });

    it('should correctly format model on changes', () => {
        component.ngOnInit();

        const value = new Date(2019, 0, 5);
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual(new NgbDate(2019, 1, 5));
    });

    it('should correctly format model on onDateSelect event', () => {
        component.ngOnInit();

        spyOn(component.valueChange, 'emit').and.stub();

        component.onDateSelect(new NgbDate(2019, 1, 5));
        expect(component.valueChange.emit).toHaveBeenCalledWith(
            new Date(2019, 0, 5)
        );
    });
});
