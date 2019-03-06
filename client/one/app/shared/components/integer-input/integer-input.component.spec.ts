import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SimpleChange} from '@angular/core';
import {IntegerInputComponent} from './integer-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event.directive';
import {FocusDirective} from '../../directives/focus.directive';

describe('IntegerInputComponent', () => {
    let component: IntegerInputComponent;
    let fixture: ComponentFixture<IntegerInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                IntegerInputComponent,
                FilterKeydownEventDirective,
                FocusDirective,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(IntegerInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        component.ngOnInit();
        expect(component).toBeDefined();
    });

    it('should correctly emit model on blur event', () => {
        spyOn(component.inputBlur, 'emit').and.stub();
        component.ngOnInit();

        const value = '1234';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('1234');

        component.model = '7871234';

        component.onBlur();
        expect(component.inputBlur.emit).toHaveBeenCalledWith('7871234');
    });

    it('should not emit model on blur event if model did not change', () => {
        spyOn(component.inputBlur, 'emit').and.stub();
        component.ngOnInit();

        const value = '1234';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('1234');

        component.onBlur();
        expect(component.model).toEqual('1234');
        expect(component.inputBlur.emit).not.toHaveBeenCalled();
    });

    it('should prevent keydown event', () => {
        component.ngOnInit();

        const $event: any = {
            preventDefault: () => {},
            key: 'a',
            target: {
                selectionStart: 0,
            },
        };
        spyOn($event, 'preventDefault').and.stub();

        component.onKeydown($event);
        expect($event.preventDefault).toHaveBeenCalled();
    });

    it('should not prevent keydown event', () => {
        component.ngOnInit();

        const $event: any = {
            preventDefault: () => {},
            key: '5',
            target: {
                selectionStart: 0,
            },
        };
        spyOn($event, 'preventDefault').and.stub();

        component.onKeydown($event);
        expect($event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent paste event', () => {
        component.ngOnInit();

        const $event: any = {
            preventDefault: () => {},
            clipboardData: {
                getData: () => {
                    return '12345.9937';
                },
            },
            target: {
                selectionStart: 0,
            },
        };
        spyOn($event, 'preventDefault').and.stub();

        component.onPaste($event);
        expect($event.preventDefault).toHaveBeenCalled();
    });

    it('should not prevent paste event', () => {
        component.ngOnInit();

        const $event: any = {
            preventDefault: () => {},
            clipboardData: {
                getData: () => {
                    return '1234567';
                },
            },
            target: {
                selectionStart: 0,
            },
        };
        spyOn($event, 'preventDefault').and.stub();

        component.onPaste($event);
        expect($event.preventDefault).not.toHaveBeenCalled();
    });
});
