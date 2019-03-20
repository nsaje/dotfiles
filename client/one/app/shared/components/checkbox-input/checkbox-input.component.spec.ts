import {TestBed, ComponentFixture} from '@angular/core/testing';
import {CheckboxInputComponent} from './checkbox-input.component';

describe('CheckboxInputComponent', () => {
    let component: CheckboxInputComponent;
    let fixture: ComponentFixture<CheckboxInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CheckboxInputComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CheckboxInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
