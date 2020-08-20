import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ListGroupItemComponent} from './list-group-item.component';
import {NewFeatureDirective} from '../../../../directives/new-feature/new-feature.directive';

describe('ListGroupItemComponent', () => {
    let component: ListGroupItemComponent;
    let fixture: ComponentFixture<ListGroupItemComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ListGroupItemComponent, NewFeatureDirective],
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
        component.selectedItemPath = ['item1', 'subitem1'];
        component.parentItemPath = [];
        component.isParentExpanded = true;
        component.isDisplayValueVisible = true;
        component.ngOnChanges();

        expect(component.isExpanded).toBeTrue();
        expect(component.isSelected).toBeFalse();
    });

    it('should be selected when in dock mode', () => {
        component.selectedItemPath = ['item1', 'subitem1'];
        component.parentItemPath = [];
        component.isParentExpanded = true;
        component.isDisplayValueVisible = false;
        component.ngOnChanges();

        expect(component.isSelected).toBeTrue();
    });

    it('should be not selected and not expanded when parent is not expanded', () => {
        component.selectedItemPath = ['item1', 'subitem1'];
        component.parentItemPath = ['item1'];
        component.isParentExpanded = false;
        component.isDisplayValueVisible = true;
        component.ngOnChanges();

        expect(component.isExpanded).toBeFalse();
        expect(component.isSelected).toBeFalse();
    });
});
