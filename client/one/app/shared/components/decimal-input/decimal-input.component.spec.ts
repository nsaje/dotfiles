import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {DebugElement, SimpleChange} from '@angular/core';
import {DecimalInputComponent} from './decimal-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event.directive';

describe('DecimalInputComponent', () => {
    let component: DecimalInputComponent;
    let fixture: ComponentFixture<DecimalInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DecimalInputComponent, FilterKeydownEventDirective],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DecimalInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        component.ngOnInit();
        expect(component).toBeDefined();
    });

    it('should correctly emit model on blur event', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.ngOnInit();

        const value = '1234.12';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('1234.12');

        component.model = '7871234.1';

        component.onBlur();
        expect(component.valueChange.emit).toHaveBeenCalledWith('7871234.10');
    });

    it('should not emit model on blur event if model did not change', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.ngOnInit();

        const value = '1234.12';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('1234.12');

        component.onBlur();
        expect(component.model).toEqual('1234.12');
        expect(component.valueChange.emit).not.toHaveBeenCalled();
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
                    return '12345.test,.,9937';
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
                    return '12345.67';
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