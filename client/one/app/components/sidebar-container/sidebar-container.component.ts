import './sidebar-container.component.less';

import {SidebarContainer} from 'ng-sidebar';
import {Component, ChangeDetectionStrategy} from '@angular/core';

@Component({
    selector: 'zem-sidebar-container',
    templateUrl: './sidebar-container.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarContainerComponent extends SidebarContainer {}
