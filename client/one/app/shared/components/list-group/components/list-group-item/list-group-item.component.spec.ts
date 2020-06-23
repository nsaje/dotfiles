import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ListGroupItemComponent} from './list-group-item.component';
import {SimpleChange} from '@angular/core';

describe('ListGroupItemComponent', () => {
    let component: ListGroupItemComponent;
    let fixture: ComponentFixture<ListGroupItemComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ListGroupItemComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ListGroupItemComponent);
        component = fixture.componentInstance;
        component.item = {
            value: 'item1',
            displayValue: 'Item 1',
            isVisible: () => true,
            subItems: [
                {
                    value: 'subitem1',
                    displayValue: 'SubItem 1-1',
                    isVisible: () => true,
                },
                {
                    value: 'subitem2',
                    displayValue: 'SubItem 1-2',
                    isVisible: () => true,
                },
            ],
        };
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should be expanded and not selected when not in dock mode', () => {
        component.value = 'subitem1';
        component.isParentExpanded = true;
        component.isDisplayValueVisible = true;
        component.ngOnChanges({
            value: new SimpleChange(null, component.value, false),
        });

        expect(component.isExpanded).toBeTrue();
        expect(component.isSelected).toBeFalse();
    });

    it('should be selected when in dock mode', () => {
        component.value = 'subitem1';
        component.isParentExpanded = true;
        component.isDisplayValueVisible = false;
        component.ngOnChanges({
            value: new SimpleChange(null, component.value, false),
        });

        expect(component.isSelected).toBeTrue();
    });

    it('should be not selected and not expanded when parent is not expanded', () => {
        component.value = 'subitem1';
        component.isParentExpanded = false;
        component.isDisplayValueVisible = true;
        component.ngOnChanges({
            value: new SimpleChange(null, component.value, false),
        });

        expect(component.isExpanded).toBeFalse();
        expect(component.isSelected).toBeFalse();
    });
});
