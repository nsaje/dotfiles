import {ComponentFixture, TestBed} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ImageCheckboxInputComponent} from './image-checkbox-input.component';
import {CheckboxInputComponent} from '../checkbox-input/checkbox-input.component';

describe('ImageCheckboxInputComponent', () => {
    let component: ImageCheckboxInputComponent;
    let fixture: ComponentFixture<ImageCheckboxInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CheckboxInputComponent, ImageCheckboxInputComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ImageCheckboxInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
