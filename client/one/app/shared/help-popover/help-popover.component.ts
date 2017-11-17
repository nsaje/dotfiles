import {
    Directive, Input, OnInit, OnChanges, DoCheck, OnDestroy, ElementRef, Inject, Injector, SimpleChanges
} from '@angular/core';
import {UpgradeComponent} from '@angular/upgrade/static';

@Directive({
    selector: 'zem-help-popover', // tslint:disable-line directive-selector
})
export class HelpPopoverComponent extends UpgradeComponent implements OnInit, OnChanges, DoCheck, OnDestroy { // tslint:disable-line directive-class-suffix max-line-length
    @Input() content: string;
    @Input() placement: string;

    constructor (@Inject(ElementRef) elementRef: ElementRef, @Inject(Injector) injector: Injector) {
        super('zemHelpPopover', elementRef, injector);
    }

    ngOnInit () { super.ngOnInit(); }
    ngOnChanges (changes: SimpleChanges) { super.ngOnChanges(changes); }
    ngDoCheck () { super.ngDoCheck(); }
    ngOnDestroy () { super.ngOnDestroy(); }
}
