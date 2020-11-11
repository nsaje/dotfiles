import {Directive, ElementRef, forwardRef, Inject, Input} from '@angular/core';
import {NgbDropdownAnchor, NgbDropdownToggle} from '@ng-bootstrap/ng-bootstrap';
import {DropdownDirective} from './dropdown.directive';

@Directive({
    selector: '[zemDropdownAnchor]',
    exportAs: 'zemDropdownAnchor',
    host: {
        class: 'zem-dropdown__toggle',
        '[class.zem-dropdown__toggle--disabled]': 'dropdown.isDropdownDisabled',
    },
})
export class DropdownAnchorDirective extends NgbDropdownAnchor {
    constructor(
        @Inject(forwardRef(() => DropdownDirective)) public dropdown: any,
        elementRef: ElementRef<HTMLElement>
    ) {
        super(dropdown, elementRef);
    }
}

// tslint:disable-next-line: max-classes-per-file
@Directive({
    selector: '[zemDropdownToggle]',
    exportAs: 'zemDropdownToggle',
    host: {
        class: 'zem-dropdown__toggle',
        '[class.zem-dropdown__toggle--disabled]': 'dropdown.isDropdownDisabled',
        '(click)': 'dropdown.toggle()',
        '(keydown.ArrowUp)': 'dropdown.onKeyDown($event)',
        '(keydown.ArrowDown)': 'dropdown.onKeyDown($event)',
        '(keydown.Home)': 'dropdown.onKeyDown($event)',
        '(keydown.End)': 'dropdown.onKeyDown($event)',
        '(keydown.Tab)': 'dropdown.onKeyDown($event)',
        '(keydown.Shift.Tab)': 'dropdown.onKeyDown($event)',
    },
    providers: [
        {
            provide: DropdownAnchorDirective,
            useExisting: forwardRef(() => DropdownToggleDirective),
        },
    ],
})
export class DropdownToggleDirective extends NgbDropdownToggle {
    constructor(
        @Inject(forwardRef(() => DropdownDirective)) public dropdown: any,
        elementRef: ElementRef<HTMLElement>
    ) {
        super(dropdown, elementRef);
    }
}
