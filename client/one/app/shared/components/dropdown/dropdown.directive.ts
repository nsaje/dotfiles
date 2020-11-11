import './dropdown.directive.less';

import {
    AfterViewInit,
    ContentChild,
    Directive,
    Input,
    OnChanges,
    SimpleChange,
    SimpleChanges,
} from '@angular/core';
import {NgbDropdown} from '@ng-bootstrap/ng-bootstrap';
import {DropdownContentDirective} from './dropdown-content.directive';
import {DropdownAnchorDirective} from './dropdown-toggle.directive';
import {Placement} from '../../types/placement';

@Directive({
    selector: '[zemDropdown]',
    exportAs: 'zemDropdown',
    host: {
        class: 'zem-dropdown',
        '[class.zem-dropdown--disabled]': 'isDropdownDisabled',
        '[class.zem-dropdown--suppress-mobile-style]':
            'suppressDropdownMobileStyle',
    },
})
export class DropdownDirective extends NgbDropdown
    implements OnChanges, AfterViewInit {
    @Input()
    isDropdownDisabled: boolean = false;
    @Input()
    dropdownPlacement: Placement;
    @Input()
    suppressDropdownMobileStyle: boolean = false;
    @Input()
    dropdownContainer: string;

    @ContentChild(DropdownContentDirective, {static: false})
    menu: DropdownContentDirective;
    @ContentChild(DropdownAnchorDirective, {static: false})
    anchor: DropdownAnchorDirective;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.dropdownPlacement) {
            changes.placement = new SimpleChange(
                this.placement,
                this.dropdownPlacement,
                false
            );
            this.placement = changes.dropdownPlacement.currentValue;
        }
        if (changes.dropdownContainer) {
            changes.container = new SimpleChange(
                this.container,
                this.dropdownContainer,
                false
            );
            this.container = changes.dropdownContainer.currentValue;
        }
        super.ngOnChanges(changes);
    }

    ngAfterViewInit(): void {
        (this as any)._menu = this.menu;
        (this as any)._anchor = this.anchor;
    }

    open(): void {
        if (this.isDropdownDisabled) {
            return;
        }
        super.open();
    }
}
