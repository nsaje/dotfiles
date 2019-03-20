import {
    Directive,
    ElementRef,
    Input,
    OnInit,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';

@Directive({
    selector: '[zemFocus]',
})
export class FocusDirective implements OnInit, OnChanges {
    @Input()
    zemFocus: boolean = true;

    constructor(private elementRef: ElementRef) {}

    ngOnInit(): void {
        this.handleFocus(this.zemFocus);
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.zemFocus) {
            this.handleFocus(this.zemFocus);
        }
    }

    private handleFocus(doFocus: boolean): void {
        if (
            !commonHelpers.isDefined(doFocus) ||
            doFocus.toString() === '' ||
            doFocus.toString() === 'true'
        ) {
            this.elementRef.nativeElement.focus();
        }
    }
}
