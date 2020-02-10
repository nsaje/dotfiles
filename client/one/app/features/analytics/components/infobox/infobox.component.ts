import {
    Directive,
    OnInit,
    OnChanges,
    DoCheck,
    OnDestroy,
    ElementRef,
    Inject,
    Injector,
    SimpleChanges,
    Input,
} from '@angular/core';
import {UpgradeComponent} from '@angular/upgrade/static';

@Directive({
    selector: 'zem-infobox', // tslint:disable-line directive-selector
})
export class InfoboxComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    entity: any;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemInfobox', elementRef, injector);
    }

    ngOnInit() {
        super.ngOnInit();
    }
    ngOnChanges(changes: SimpleChanges) {
        super.ngOnChanges(changes);
    }
    ngDoCheck() {
        super.ngDoCheck();
    }
    ngOnDestroy() {
        super.ngOnDestroy();
    }
}
