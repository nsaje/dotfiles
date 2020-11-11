import {Directive, ElementRef, forwardRef, Inject} from '@angular/core';
import {NgbDropdownMenu} from '@ng-bootstrap/ng-bootstrap';
import {DropdownDirective} from './dropdown.directive';

@Directive({
    selector: '[zemDropdownContent]',
    exportAs: 'zemDropdownContent',
    host: {
        class: 'zem-dropdown__content',
        '[class.zem-dropdown__content--open]': 'dropdown.isOpen()',
        '[class.zem-dropdown__content--disabled]':
            'dropdown.isDropdownDisabled',
        '[attr.x-placement]': 'placement',
        '(keydown.ArrowUp)': 'dropdown.onKeyDown($event)',
        '(keydown.ArrowDown)': 'dropdown.onKeyDown($event)',
        '(keydown.Home)': 'dropdown.onKeyDown($event)',
        '(keydown.End)': 'dropdown.onKeyDown($event)',
        '(keydown.Enter)': 'dropdown.onKeyDown($event)',
        '(keydown.Space)': 'dropdown.onKeyDown($event)',
        '(keydown.Tab)': 'dropdown.onKeyDown($event)',
        '(keydown.Shift.Tab)': 'dropdown.onKeyDown($event)',
    },
})
export class DropdownContentDirective extends NgbDropdownMenu {
    constructor(
        @Inject(forwardRef(() => DropdownDirective))
        dropdown: any,
        elementRef: ElementRef<HTMLElement>
    ) {
        super(dropdown, elementRef);
    }
}
