import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ItemListComponent} from './item-list.component';
import Spy = jasmine.Spy;

describe('ItemListComponent', () => {
    let component: ItemListComponent<any>;
    let fixture: ComponentFixture<ItemListComponent<any>>;

    const mockedItems: string[] = [
        'notSelected',
        'alreadySelected',
        'anotherItem',
    ];
    let selectedItemsChangeSpy: Spy;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ItemListComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ItemListComponent);
        component = fixture.componentInstance;
    });

    function testSelectedItemsChange(
        multiple: boolean,
        canSelectNone: boolean,
        ctrlKey: boolean,
        alreadySelectedItems: 1 | 2,
        clickedItem: string,
        expectedOutput: string[]
    ) {
        selectedItemsChangeSpy.calls.reset();
        component.multiple = multiple;
        component.canSelectNone = canSelectNone;
        component.items = mockedItems;
        if (alreadySelectedItems === 1) {
            component.selectedItems = ['alreadySelected'];
        } else {
            component.selectedItems = ['alreadySelected', 'anotherItem'];
        }
        const mouseEvent: MouseEvent = <MouseEvent>{ctrlKey};

        component.clickItem(mouseEvent, clickedItem);

        if (expectedOutput === undefined) {
            expect(component.selectedItemsChange.emit).not.toHaveBeenCalled();
        } else {
            expect(component.selectedItemsChange.emit).toHaveBeenCalledWith(
                expectedOutput
            );
        }
    }

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should produce the correct output on item click', () => {
        selectedItemsChangeSpy = spyOn(
            component.selectedItemsChange,
            'emit'
        ).and.stub();
        testSelectedItemsChange(false, false, false, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, false, false, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(false, true, false, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, true, false, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(false, false, true, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, false, true, 1, 'notSelected', [
            'alreadySelected',
            'notSelected',
        ]);
        testSelectedItemsChange(false, true, true, 1, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, true, true, 1, 'notSelected', [
            'alreadySelected',
            'notSelected',
        ]);
        testSelectedItemsChange(false, false, false, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, false, false, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(false, true, false, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, true, false, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(false, false, true, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, false, true, 2, 'notSelected', [
            'alreadySelected',
            'anotherItem',
            'notSelected',
        ]);
        testSelectedItemsChange(false, true, true, 2, 'notSelected', [
            'notSelected',
        ]);
        testSelectedItemsChange(true, true, true, 2, 'notSelected', [
            'alreadySelected',
            'anotherItem',
            'notSelected',
        ]);

        testSelectedItemsChange(
            false,
            false,
            false,
            1,
            'alreadySelected',
            undefined
        );
        testSelectedItemsChange(
            true,
            false,
            false,
            1,
            'alreadySelected',
            undefined
        );
        testSelectedItemsChange(false, true, false, 1, 'alreadySelected', []);
        testSelectedItemsChange(true, true, false, 1, 'alreadySelected', []);
        testSelectedItemsChange(
            false,
            false,
            true,
            1,
            'alreadySelected',
            undefined
        );
        testSelectedItemsChange(
            true,
            false,
            true,
            1,
            'alreadySelected',
            undefined
        );
        testSelectedItemsChange(false, true, true, 1, 'alreadySelected', []);
        testSelectedItemsChange(true, true, true, 1, 'alreadySelected', []);
        testSelectedItemsChange(false, false, false, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(true, false, false, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(false, true, false, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(true, true, false, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(false, false, true, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(true, false, true, 2, 'alreadySelected', [
            'anotherItem',
        ]);
        testSelectedItemsChange(false, true, true, 2, 'alreadySelected', [
            'alreadySelected',
        ]);
        testSelectedItemsChange(true, true, true, 2, 'alreadySelected', [
            'anotherItem',
        ]);
    });
});
