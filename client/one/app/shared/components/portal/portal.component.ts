import {
    Component,
    ChangeDetectionStrategy,
    Input,
    AfterViewInit,
    OnDestroy,
    ViewChild,
    ComponentFactoryResolver,
    ApplicationRef,
    Injector,
} from '@angular/core';
import {CdkPortal, DomPortalHost} from '@angular/cdk/portal';
import * as commonHelpers from '../../helpers/common.helpers';

@Component({
    selector: 'zem-portal',
    templateUrl: './portal.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PortalComponent implements AfterViewInit, OnDestroy {
    @Input()
    hostElementId: string;

    @ViewChild(CdkPortal)
    portal: CdkPortal;

    portalHost: DomPortalHost;

    constructor(
        private componentFactoryResolver: ComponentFactoryResolver,
        private applicationRef: ApplicationRef,
        private injector: Injector
    ) {}

    ngAfterViewInit(): void {
        this.portalHost = new DomPortalHost(
            document.getElementById(this.hostElementId),
            this.componentFactoryResolver,
            this.applicationRef,
            this.injector
        );
        this.portalHost.attach(this.portal);
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.portalHost)) {
            this.portalHost.detach();
        }
    }
}
