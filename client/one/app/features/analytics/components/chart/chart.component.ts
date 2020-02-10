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
import {Level, Breakdown} from '../../../../app.constants';

@Directive({
    selector: 'zem-chart', // tslint:disable-line directive-selector
})
export class ChartComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    level: Level;
    @Input()
    breakdown: Breakdown;
    @Input()
    entityId: string;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemChart', elementRef, injector);
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
