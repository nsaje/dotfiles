import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SelectListComponent} from './select-list.component';
import {SelectInputComponent} from '../select-input/select-input.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {SimpleChange} from '@angular/core';
import {group} from '@angular/animations';
import {LoaderComponent} from '../loader/loader.component';

describe('SelectListComponent', () => {
    let component: SelectListComponent;
    let fixture: ComponentFixture<SelectListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                SelectInputComponent,
                TextHighlightDirective,
                SelectListComponent,
                LoaderComponent,
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

    it('should correctly emit itemSelect event', () => {
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

        spyOn(component.itemSelect, 'emit').and.stub();

        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            availableItems: new SimpleChange(null, availableItems, false),
        });

        expect(component.availableItemsFiltered).toEqual([
            {name: 'Katja', value: 4},
            {name: 'Matjaz', value: 5},
        ]);

        component.onItemSelect(5);
        expect(component.itemSelect.emit).toHaveBeenCalledWith({
            name: 'Matjaz',
            value: 5,
        });
        (<any>component.itemSelect.emit).calls.reset();

        component.onItemSelect(null);
        expect(component.itemSelect.emit).not.toHaveBeenCalled();
        (<any>component.itemSelect.emit).calls.reset();
    });

    it('should correctly limit items', () => {
        const bindValue = 'value';
        const selectedItems: any[] = [
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
        ];
        let itemListLimit = 2;

        component.bindValue = bindValue;
        component.selectedItems = selectedItems;
        component.availableItems = [];
        component.itemListLimit = itemListLimit;

        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            itemListLimit: new SimpleChange(null, itemListLimit, false),
        });

        expect(component.selectedItemsLimited).toEqual([
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
        ]);

        itemListLimit = null;
        component.itemListLimit = itemListLimit;
        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            itemListLimit: new SimpleChange(2, itemListLimit, false),
        });

        expect(component.selectedItemsLimited).toEqual([
            {name: 'Nejc', value: 1},
            {name: 'Anej', value: 2},
            {name: 'Jure', value: 3},
        ]);
    });

    it('should correctly group and limit items', () => {
        const bindValue = 'value';
        const selectedItems: any[] = [
            {name: 'Nejc', type: 'male', value: 1},
            {name: 'Anej', type: 'male', value: 2},
            {name: 'Jure', type: 'male', value: 3},
            {name: 'Katja', type: 'female', value: 4},
            {name: 'Petra', type: 'female', value: 5},
        ];

        const groupByValue = 'type';
        let itemListLimitByGroup = {
            male: 1,
            female: 1,
        };

        component.bindValue = bindValue;
        component.selectedItems = selectedItems;
        component.availableItems = [];
        component.groupByValue = groupByValue;
        component.itemListLimitByGroup = itemListLimitByGroup;

        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            groupByValue: new SimpleChange(null, groupByValue, false),
            itemListLimitByGroup: new SimpleChange(
                null,
                itemListLimitByGroup,
                false
            ),
        });

        expect(component.selectedItemsGroupedLimited).toEqual([
            {
                groupName: 'male',
                items: [
                    {name: 'Nejc', type: 'male', value: 1},
                    {name: 'Anej', type: 'male', value: 2},
                    {name: 'Jure', type: 'male', value: 3},
                ],
                limitedItems: [{name: 'Nejc', type: 'male', value: 1}],
            },
            {
                groupName: 'female',
                items: [
                    {name: 'Katja', type: 'female', value: 4},
                    {name: 'Petra', type: 'female', value: 5},
                ],
                limitedItems: [{name: 'Katja', type: 'female', value: 4}],
            },
        ]);

        itemListLimitByGroup = {
            male: null,
            female: null,
        };
        component.itemListLimitByGroup = itemListLimitByGroup;
        component.ngOnChanges({
            bindValue: new SimpleChange(null, bindValue, false),
            selectedItems: new SimpleChange(null, selectedItems, false),
            groupByValue: new SimpleChange(null, groupByValue, false),
            itemListLimitByGroup: new SimpleChange(
                null,
                itemListLimitByGroup,
                false
            ),
        });

        expect(component.selectedItemsGroupedLimited).toEqual([
            {
                groupName: 'male',
                items: [
                    {name: 'Nejc', type: 'male', value: 1},
                    {name: 'Anej', type: 'male', value: 2},
                    {name: 'Jure', type: 'male', value: 3},
                ],
                limitedItems: [
                    {name: 'Nejc', type: 'male', value: 1},
                    {name: 'Anej', type: 'male', value: 2},
                    {name: 'Jure', type: 'male', value: 3},
                ],
            },
            {
                groupName: 'female',
                items: [
                    {name: 'Katja', type: 'female', value: 4},
                    {name: 'Petra', type: 'female', value: 5},
                ],
                limitedItems: [
                    {name: 'Katja', type: 'female', value: 4},
                    {name: 'Petra', type: 'female', value: 5},
                ],
            },
        ]);
    });
});
