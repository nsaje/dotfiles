import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {NgSelectModule} from '@ng-select/ng-select';
import {SelectInputComponent} from './select-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {SimpleChange} from '@angular/core';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('SelectInputComponent', () => {
    let component: SelectInputComponent;
    let fixture: ComponentFixture<SelectInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                FocusDirective,
                TextHighlightDirective,
                SelectInputComponent,
                LoaderComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SelectInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should be correctly initialized on input change', () => {
        const bindLabel = 'name';
        const bindValue = 'value';
        const items: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
        ];
        const orderByValue = 'name';

        component.bindLabel = bindLabel;
        component.bindValue = bindValue;
        component.items = items;
        component.orderByValue = orderByValue;

        component.ngOnChanges({
            bindLabel: new SimpleChange(null, bindLabel, false),
            bindValue: new SimpleChange(null, bindValue, false),
            items: new SimpleChange(null, items, false),
            orderByValue: new SimpleChange(null, orderByValue, false),
        });

        expect(component.formattedItems).toEqual([
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
            {name: 'Nejc', value: 1},
        ]);
    });

    it('should correctly emit model on change event', () => {
        component.bindValue = 'value';

        spyOn(component.valueChange, 'emit').and.stub();

        component.onChange({value: 'TEST'});
        expect(component.valueChange.emit).toHaveBeenCalledWith('TEST');
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(undefined);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(null);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
    });

    it('should correctly emit model on change event with isMultiple = true', () => {
        component.bindValue = 'value';

        spyOn(component.valueChange, 'emit').and.stub();

        component.onChange([
            {name: 'Anej', value: '2'},
            {name: 'Jure', value: '3'},
            {name: 'Nejc', value: '1'},
        ]);
        expect(component.valueChange.emit).toHaveBeenCalledWith([
            '2',
            '3',
            '1',
        ]);
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(undefined);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(null);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
    });
});
