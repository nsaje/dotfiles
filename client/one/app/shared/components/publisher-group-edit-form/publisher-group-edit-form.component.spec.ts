import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {PublisherGroupEditFormComponent} from './publisher-group-edit-form.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
import {TextFormGroupComponent} from '../text-form-group/text-form-group.component';
import {CheckboxFormGroupComponent} from '../checkbox-form-group/checkbox-form-group.component';
import {ContentFormGroupComponent} from '../content-form-group/content-form-group.component';
import {FileSelectorComponent} from '../file-selector/file-selector.component';
import {HelpPopoverComponent} from '../help-popover/help-popover.component';
import {TextInputComponent} from '../text-input/text-input.component';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';
import {PopoverDirective} from '../popover/popover.directive';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('PublisherGroupEditFormComponent', () => {
    let component: PublisherGroupEditFormComponent;
    let fixture: ComponentFixture<PublisherGroupEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                PublisherGroupEditFormComponent,
                TextFormGroupComponent,
                CheckboxFormGroupComponent,
                ContentFormGroupComponent,
                FileSelectorComponent,
                HelpPopoverComponent,
                TextInputComponent,
                CheckboxInputComponent,
                LoaderComponent,
                PopoverDirective,
                FocusDirective,
            ],
            imports: [FormsModule, NgSelectModule, NgbDatepickerModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(PublisherGroupEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
