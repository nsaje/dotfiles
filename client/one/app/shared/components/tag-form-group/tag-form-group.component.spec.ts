import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {TagFormGroupComponent} from './tag-form-group.component';
import {TagPickerComponent} from '../tag-picker/tag-picker.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {SelectInputComponent} from '../select-input/select-input.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {PopoverDirective} from '../popover/popover.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('TagFormGroupComponent', () => {
    let component: TagFormGroupComponent;
    let fixture: ComponentFixture<TagFormGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                FocusDirective,
                TextHighlightDirective,
                SelectInputComponent,
                TagPickerComponent,
                TagFormGroupComponent,
                PopoverDirective,
                HelpPopoverComponent,
                LoaderComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TagFormGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
