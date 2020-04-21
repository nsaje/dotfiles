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
import {Breakdown, Level} from '../../../../../app.constants';

@Directive({
    selector: 'zem-grid-container', // tslint:disable-line directive-selector
})
export class GridContainerComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    level: Level;
    @Input()
    breakdown: Breakdown;
    @Input()
    entity: any;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemGridContainer', elementRef, injector);
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
