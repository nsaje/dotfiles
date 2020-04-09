import {Directive, Host, HostListener} from '@angular/core';

import {DropdownDirective} from './dropdown.directive';

@Directive({
    selector: '[zemDropdownToggle]',
})
export class DropdownToggleDirective {
    constructor(@Host() private dropdown: DropdownDirective) {}

    @HostListener('click')
    toggleDropdown(): void {
        if (this.dropdown.disabled) {
            return;
        }

        if (this.dropdown.isOpen()) {
            this.dropdown.close();
        } else {
            this.dropdown.open();
        }
    }
}
