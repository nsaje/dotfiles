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
    selector: 'zem-retargeting', // tslint:disable-line directive-selector
})
export class RetargetingComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    entityId: any;
    @Input()
    retargetableAudiences: any;
    @Input()
    retargetableAdGroups: any;
    @Input()
    includedAudiences: any;
    @Input()
    excludedAudiences: any;
    @Input()
    includedAdGroups: any;
    @Input()
    excludedAdGroups: any;
    @Input()
    includedAudiencesErrors: any;
    @Input()
    excludedAudiencesErrors: any;
    @Input()
    includedAdGroupsErrors: any;
    @Input()
    excludedAdGroupsErrors: any;
    @Input()
    warnings: any;
    @Input()
    isDisabled: boolean;
    @Output()
    onUpdate: any;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemRetargeting', elementRef, injector);
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
