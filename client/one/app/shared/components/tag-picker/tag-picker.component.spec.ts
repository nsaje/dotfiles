import {TestBed, ComponentFixture} from '@angular/core/testing';
import {TagPickerComponent} from './tag-picker.component';
import {FormsModule} from '@angular/forms';
import {SelectInputComponent} from '../select-input/select-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {NgSelectModule} from '@ng-select/ng-select';
import {OnChanges, SimpleChange, SimpleChanges} from '@angular/core';
import {LoaderComponent} from '../loader/loader.component';

describe('TagPickerComponent', () => {
    let component: TagPickerComponent;
    let fixture: ComponentFixture<TagPickerComponent>;

    function changeComponent(
        component: OnChanges,
        changes: {[key: string]: any}
    ) {
        const simpleChanges: SimpleChanges = {};

        Object.keys(changes).forEach(changeKey => {
            component[changeKey] = changes[changeKey];
            simpleChanges[changeKey] = new SimpleChange(
                null,
                changes[changeKey],
                false
            );
        });
        component.ngOnChanges(simpleChanges);
    }

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                FocusDirective,
                TextHighlightDirective,
                SelectInputComponent,
                TagPickerComponent,
                LoaderComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TagPickerComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly map items to formattedItems', () => {
        expect(component.formattedItems).toEqual([]);

        changeComponent(component, {items: ['one', 'two', 'three']});

        expect(component.formattedItems).toEqual([
            {tag: 'one'},
            {tag: 'two'},
            {tag: 'three'},
        ]);

        changeComponent(component, {items: []});

        expect(component.formattedItems).toEqual([]);
    });
});
