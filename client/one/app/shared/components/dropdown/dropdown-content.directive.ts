import {Directive, ElementRef, forwardRef, Inject} from '@angular/core';
import {DropdownDirective} from './dropdown.directive';

@Directive({
    selector: '[zemDropdownContent]',
    exportAs: 'zemDropdownContent',
    host: {
        class: 'zem-dropdown__content',
        '[class.zem-dropdown__content--open]': 'dropdown.isOpen()',
        '[class.zem-dropdown__content--disabled]':
            'dropdown.isDropdownDisabled',
    },
})
export class DropdownContentDirective {
    nativeElement: HTMLElement;
    constructor(
        @Inject(forwardRef(() => DropdownDirective)) public dropdown: any,
        private elementRef: ElementRef<HTMLElement>
    ) {
        this.nativeElement = elementRef.nativeElement;
    }
}
