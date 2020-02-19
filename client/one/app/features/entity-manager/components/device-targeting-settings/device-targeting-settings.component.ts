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
    selector: 'zem-device-targeting-settings', // tslint:disable-line directive-selector
})
export class DeviceTargetingSettingsComponent extends UpgradeComponent
    implements OnInit, OnChanges, DoCheck, OnDestroy {
    @Input()
    targetDevices: any;
    @Input()
    targetEnvironments: any;
    @Input()
    targetOs: any;
    @Input()
    errors: any;
    @Output()
    onUpdate: any;

    constructor(
        @Inject(ElementRef) elementRef: ElementRef,
        @Inject(Injector) injector: Injector
    ) {
        super('zemDeviceTargetingSettings', elementRef, injector);
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
