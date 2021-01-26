import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SimpleChange} from '@angular/core';
import {TextInputComponent} from './text-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';
import {LoaderComponent} from '../loader/loader.component';

describe('TextInputComponent', () => {
    let component: TextInputComponent;
    let fixture: ComponentFixture<TextInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TextInputComponent, LoaderComponent, FocusDirective],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TextInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit model on blur event', () => {
        spyOn(component.inputBlur, 'emit').and.stub();

        const value = 'Hello world';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('Hello world');

        component.model = 'Hello world!';

        component.onBlur();
        expect(component.inputBlur.emit).toHaveBeenCalledWith('Hello world!');
    });

    it('should not emit model on blur event if model did not change', () => {
        spyOn(component.inputBlur, 'emit').and.stub();

        const value = 'Hello world';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('Hello world');

        component.onBlur();
        expect(component.model).toEqual('Hello world');
        expect(component.inputBlur.emit).not.toHaveBeenCalled();
    });
});
