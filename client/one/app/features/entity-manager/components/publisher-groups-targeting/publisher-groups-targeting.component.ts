import {
    Directive,
    Input,
    OnInit,
    OnChanges,
    DoCheck,
    OnDestroy,
    ElementRef,
    Inject,
    Injector,
    SimpleChanges,
    Output,
} from '@angular/core';
import {UpgradeComponent} from '@angular/upgrade/static';

@Directive({
    selector: 'zem-publisher-group-targeting', // tslint:disable-line directive-selector
})
export class PublisherGroupTargetingComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    accountId: any;
    @Input()
    whitelistedPublisherGroups: any;
    @Input()
    blacklistedPublisherGroups: any;
    @Input()
    whitelistedPublisherGroupsErrors: any;
    @Input()
    blacklistedPublisherGroupsErrors: any;
    @Input()
    showNewLabels: boolean;
    @Input()
    isDisabled: boolean;
    @Output()
    onUpdate: any;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemPublisherGroupTargeting', elementRef, injector);
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
