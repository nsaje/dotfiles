import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SelectListComponent} from './select-list.component';
import {SelectInputComponent} from '../select-input/select-input.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {SimpleChange} from '@angular/core';

describe('SelectListComponent', () => {
    let component: SelectListComponent;
    let fixture: ComponentFixture<SelectListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                SelectInputComponent,
                TextHighlightDirective,
                SelectListComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SelectListComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should be correctly initialized on input change', () => {
        const bindLabel = 'name';
        const bindValue = 'value';
        const selectedItems: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
        ];
        const availableItems: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
            {name: 'Katja', value: 4},
            {name: 'Matjaz', value: 5},
        ];

        component.bindLabel = bindLabel;
        component.bindValue = bindValue;
        component.selectedItems = selectedItems;
        component.availableItems = availableItems;

        component.ngOnChanges({
            bindLabel: new SimpleChange(null, bindLabel, false),
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            availableItems: new SimpleChange(null, availableItems, false),
        });

        expect(component.availableItemsFiltered).toEqual([
            {name: 'Katja', value: 4},
            {name: 'Matjaz', value: 5},
        ]);
    });

    it('should correctly emit itemSelected event', () => {
        const bindValue = 'value';
        const selectedItems: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
        ];
        const availableItems: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
            {name: 'Katja', value: 4},
            {name: 'Matjaz', value: 5},
        ];

        component.bindValue = bindValue;
        component.selectedItems = selectedItems;
        component.availableItems = availableItems;

        spyOn(component.itemSelected, 'emit').and.stub();

        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            availableItems: new SimpleChange(null, availableItems, false),
        });

        expect(component.availableItemsFiltered).toEqual([
            {name: 'Katja', value: 4},
            {name: 'Matjaz', value: 5},
        ]);

        component.onItemSelected(5);
        expect(component.itemSelected.emit).toHaveBeenCalledWith({
            name: 'Matjaz',
            value: 5,
        });
        (<any>component.itemSelected.emit).calls.reset();

        component.onItemSelected(null);
        expect(component.itemSelected.emit).not.toHaveBeenCalled();
        (<any>component.itemSelected.emit).calls.reset();
    });
});
