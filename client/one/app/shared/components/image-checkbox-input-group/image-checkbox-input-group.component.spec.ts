import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ImageCheckboxInputGroupComponent} from './image-checkbox-input-group.component';
import {ImageCheckboxInputComponent} from '../image-checkbox-input/image-checkbox-input.component';
import {ImageCheckboxInputItem} from '../image-checkbox-input/types/image-checkbox-input-item';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';
import {ImageCheckboxInputIcon} from '../image-checkbox-input/image-checkbox-input.constants';

describe('ImageCheckboxInputGroupComponent', () => {
    let component: ImageCheckboxInputGroupComponent;
    let fixture: ComponentFixture<ImageCheckboxInputGroupComponent>;

    function getItemONE(): ImageCheckboxInputItem {
        return component.formattedOptions.find(x => x.value === 'ONE');
    }
    function getItemTWO(): ImageCheckboxInputItem {
        return component.formattedOptions.find(x => x.value === 'TWO');
    }
    function getItemTHREE(): ImageCheckboxInputItem {
        return component.formattedOptions.find(x => x.value === 'THREE');
    }

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CheckboxInputComponent,
                ImageCheckboxInputComponent,
                ImageCheckboxInputGroupComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ImageCheckboxInputGroupComponent);
        component = fixture.componentInstance;

        component.options = [
            {
                value: 'ONE',
                displayValue: 'One',
                icon: ImageCheckboxInputIcon.DESKTOP,
            },
            {
                value: 'TWO',
                displayValue: 'Two',
                icon: ImageCheckboxInputIcon.DESKTOP,
            },
            {
                value: 'THREE',
                displayValue: 'Three',
                icon: ImageCheckboxInputIcon.DESKTOP,
            },
        ];
        component.ngOnChanges();
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
