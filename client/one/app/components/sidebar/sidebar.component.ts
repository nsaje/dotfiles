import './sidebar.component.less';

import {Sidebar} from 'ng-sidebar';
import {
    Component,
    Optional,
    ChangeDetectorRef,
    Inject,
    PLATFORM_ID,
    ChangeDetectionStrategy,
} from '@angular/core';
import {SidebarContainerComponent} from '../sidebar-container/sidebar-container.component';

@Component({
    selector: 'zem-sidebar',
    templateUrl: './sidebar.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent extends Sidebar {
    constructor(
        @Optional() container: SidebarContainerComponent,
        changeDetectorRef: ChangeDetectorRef,
        @Inject(PLATFORM_ID) platformId: Object
    ) {
        super(container, changeDetectorRef, platformId);
    }
}
