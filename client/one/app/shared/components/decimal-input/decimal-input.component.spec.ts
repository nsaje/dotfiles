import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {OnChanges, SimpleChange, SimpleChanges} from '@angular/core';
import {DecimalInputComponent} from './decimal-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event/filter-keydown-event.directive';
import {PrefixedInputComponent} from '../prefixed-input/prefixed-input.component';
import {FocusDirective} from '../../directives/focus/focus.directive';

describe('DecimalInputComponent', () => {
    let component: DecimalInputComponent;
    let fixture: ComponentFixture<DecimalInputComponent>;

    function createKeyboardEvent(
        key: string,
        selectionStart: number,
        selectionEnd: number
    ): KeyboardEvent {
        const keyboardEvent: any = {
            __proto__: KeyboardEvent.prototype,
            type: 'keydown',
            key: key,
            target: {
                selectionStart: selectionStart,
                selectionEnd: selectionEnd,
            },
            preventDefault: () => {},
        };

        return keyboardEvent as KeyboardEvent;
    }

    function createClipboardEvent(
        text: string,
        selectionStart: number,
        selectionEnd: number
    ): ClipboardEvent {
        const clipboardEvent: any = {
            type: 'paste',
            clipboardData: {
                getData: () => {
                    return text;
                },
            },
            target: {
                selectionStart: selectionStart,
                selectionEnd: selectionEnd,
            },
            preventDefault: () => {},
        };

        return clipboardEvent as ClipboardEvent;
    }

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

    function testEvent(
        component: DecimalInputComponent,
        $event: KeyboardEvent | ClipboardEvent,
        shouldBeValid: boolean,
        expectEmittedText?: string
    ) {
        spyOn($event, 'preventDefault').and.stub();

        component.onFocus();

        if ($event instanceof KeyboardEvent) {
            component.onKeydown($event);
        } else {
            component.onPaste($event);
        }

        if (shouldBeValid) {
            if (expectEmittedText) {
                expect(component.valueChange.emit).toHaveBeenCalledWith(
                    expectEmittedText
                );
            }
        } else {
            expect($event.preventDefault).toHaveBeenCalled();
        }
    }

    function initComponent(
        component: DecimalInputComponent,
        fractionSize: number
    ) {
        component.fractionSize = fractionSize;
        component.ngOnInit();
    }

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                PrefixedInputComponent,
                DecimalInputComponent,
                FilterKeydownEventDirective,
                FocusDirective,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DecimalInputComponent);
        component = fixture.componentInstance;
        initComponent(component, 2);

        changeComponent(component, {value: '67.89'});

        spyOn(component.valueChange, 'emit').and.stub();
        spyOn(component.inputBlur, 'emit').and.stub();
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit value on blur event', () => {
        component.onFocus();

        const $event: ClipboardEvent = createClipboardEvent('12.34', 0, 5); // 67.89 => 12.34
        component.model = '12.34';
        component.onPaste($event);

        component.onBlur();
        expect(component.inputBlur.emit).toHaveBeenCalledWith('12.34');
    });

    it('should not emit value on blur event if model did not change', () => {
        component.onFocus();
        component.model = '67.89';

        component.onBlur();
        expect(component.inputBlur.emit).not.toHaveBeenCalled();
    });

    it('should format text after component is blurred', () => {
        const $event: KeyboardEvent = createKeyboardEvent('5', 0, 5);
        testEvent(component, $event, true, '5.00');
    });

    it('should prevent keydown event for disallowed characters', () => {
        const $event: KeyboardEvent = createKeyboardEvent('a', 0, 0);
        testEvent(component, $event, false);
    });

    it('should not prevent keydown event if it results in a valid number', () => {
        let $event: KeyboardEvent = createKeyboardEvent('5', 0, 0); // 67.89 => 567.89
        testEvent(component, $event, true, '567.89');

        component.model = '67.89';
        $event = createKeyboardEvent('5', 1, 1); // 67.89 => 657.89
        testEvent(component, $event, true, '657.89');

        component.model = '67.89';
        $event = createKeyboardEvent('5', 2, 3); // 67.89 => 67589
        testEvent(component, $event, true, '67589.00');
    });

    it('should prevent keydown event if it results in an invalid number', () => {
        const $event: KeyboardEvent = createKeyboardEvent('5', 5, 5); // 67.89 => 67.895
        testEvent(component, $event, false);
    });

    it('should not prevent keydown event if the result is below the maximum allowed', () => {
        changeComponent(component, {maxValue: 500});
        const $event: KeyboardEvent = createKeyboardEvent('4', 0, 0); // 67.89 => 467.89
        testEvent(component, $event, true, '467.89');
    });

    it('should prevent keydown event if the result is above the maximum allowed', () => {
        changeComponent(component, {maxValue: 500});
        const $event: KeyboardEvent = createKeyboardEvent('5', 0, 0); // 67.89 => 567.89
        testEvent(component, $event, false);
    });

    it('should not prevent keydown event if the result is above the minimum allowed', () => {
        changeComponent(component, {minValue: 50});
        const $event: KeyboardEvent = createKeyboardEvent('1', 0, 0); // 67.89 => 167.89
        testEvent(component, $event, true, '167.89');
    });

    it('should prevent keydown event if the result is below the minimum allowed', () => {
        changeComponent(component, {minValue: 50});
        const $event: KeyboardEvent = createKeyboardEvent('-', 0, 0); // 67.89 => -67.89
        testEvent(component, $event, false);
    });

    it('should prevent paste event of disallowed values', () => {
        const $event: ClipboardEvent = createClipboardEvent(
            '12345.test,.,9937',
            0,
            5
        );
        testEvent(component, $event, false);
    });

    it('should not prevent paste event of allowed values', () => {
        let $event: ClipboardEvent = createClipboardEvent('12.67', 0, 5); // 67.89 => 12.67
        testEvent(component, $event, true, '12.67');

        $event = createClipboardEvent('12.6', 1, 4); // 67.89 => 612.69
        testEvent(component, $event, true, '612.69');
    });

    it('should prevent paste event if it results in an invalid number', () => {
        const $event: ClipboardEvent = createClipboardEvent('12.67', 0, 0); // 67.89 => 12.6767.89
        testEvent(component, $event, false);
    });

    it('should not prevent paste event if the result is below the maximum allowed', () => {
        changeComponent(component, {maxValue: 1000});
        const $event: ClipboardEvent = createClipboardEvent('800', 0, 5); // 67.89 => 800

        testEvent(component, $event, true, '800.00');
    });

    it('should prevent paste event if the result is above the maximum allowed', () => {
        changeComponent(component, {maxValue: 1000});
        const $event: ClipboardEvent = createClipboardEvent('1234', 0, 5); // 67.89 => 1234
        testEvent(component, $event, false);
    });

    it('should not prevent paste event if the result is above the minimum allowed', () => {
        changeComponent(component, {minValue: -1000});
        const $event: ClipboardEvent = createClipboardEvent('-800', 0, 5); // 67.89 => -800
        testEvent(component, $event, true, '-800.00');
    });

    it('should prevent paste event if the result is below the minimum allowed', () => {
        changeComponent(component, {minValue: -1000});
        const $event: ClipboardEvent = createClipboardEvent('-1234', 0, 5); // 67.89 => -1234
        testEvent(component, $event, false);
    });

    it('should allow numbers with less than the specified number of decimals', () => {
        initComponent(component, 5);
        const $event: ClipboardEvent = createClipboardEvent('123.4567', 0, 5); // 67.89 => 123.4567
        testEvent(component, $event, true, '123.45670');
    });

    it('should not allow numbers with more than the specified number of decimals', () => {
        initComponent(component, 3);
        const $event: ClipboardEvent = createClipboardEvent('123.4567', 0, 5); // 67.89 => 123.4567
        testEvent(component, $event, false);
    });
});
