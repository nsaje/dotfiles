import {Directive, ElementRef, forwardRef, Inject} from '@angular/core';
import {DropdownDirective} from './dropdown.directive';

@Directive({
    selector: '[zemDropdownToggle]',
    exportAs: 'zemDropdownToggle',
    host: {
        class: 'zem-dropdown__toggle',
        '[class.zem-dropdown__toggle--disabled]': 'dropdown.isDropdownDisabled',
        '(click)': 'dropdown.toggle()',
    },
})
export class DropdownToggleDirective {
    nativeElement: HTMLElement;
    constructor(
        @Inject(forwardRef(() => DropdownDirective)) public dropdown: any,
        private elementRef: ElementRef<HTMLElement>
    ) {
        this.nativeElement = elementRef.nativeElement;
    }
}
