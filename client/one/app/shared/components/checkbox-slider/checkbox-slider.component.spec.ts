import {TestBed, ComponentFixture} from '@angular/core/testing';
import {CheckboxSliderComponent} from './checkbox-slider.component';
import Spy = jasmine.Spy;
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';

describe('CheckboxSliderComponent', () => {
    let component: CheckboxSliderComponent<string>;
    let fixture: ComponentFixture<CheckboxSliderComponent<any>>;
    let selectionChangeSpy: Spy;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CheckboxSliderComponent, CheckboxInputComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CheckboxSliderComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should select all items before the selected one', () => {
        component.options = [
            {value: '1', displayValue: 'one', selected: false},
            {value: '2', displayValue: 'two', selected: undefined},
            {value: '3', displayValue: 'three', selected: false},
            {value: '4', displayValue: 'four', selected: undefined},
            {value: '5', displayValue: 'five', selected: false},
        ];

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggle(true, 2);

        expect(component.selectionChange.emit).toHaveBeenCalledWith([
            {value: '1', displayValue: 'one', selected: true},
            {value: '2', displayValue: 'two', selected: true},
            {value: '3', displayValue: 'three', selected: true},
            {value: '4', displayValue: 'four', selected: undefined},
            {value: '5', displayValue: 'five', selected: false},
        ]);
    });

    it('should deselect all items after the selected one', () => {
        component.options = [
            {value: '1', displayValue: 'one', selected: true},
            {value: '2', displayValue: 'two', selected: undefined},
            {value: '3', displayValue: 'three', selected: true},
            {value: '4', displayValue: 'four', selected: undefined},
            {value: '5', displayValue: 'five', selected: true},
        ];

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggle(false, 2);

        expect(component.selectionChange.emit).toHaveBeenCalledWith([
            {value: '1', displayValue: 'one', selected: true},
            {value: '2', displayValue: 'two', selected: undefined},
            {value: '3', displayValue: 'three', selected: false},
            {value: '4', displayValue: 'four', selected: false},
            {value: '5', displayValue: 'five', selected: false},
        ]);
    });
});
