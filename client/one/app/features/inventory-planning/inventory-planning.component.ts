import './inventory-planning.component.less';

import {Component, Inject, ChangeDetectionStrategy} from '@angular/core';

import {InventoryPlanningStore} from './inventory-planning.store';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';

@Component({
    selector: 'zem-inventory-planning',
    templateUrl: './inventory-planning.component.html',
    providers: [InventoryPlanningStore, InventoryPlanningEndpoint],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningComponent {
    constructor (private store: InventoryPlanningStore, @Inject('zemPermissions') private zemPermissions: any) {}  // tslint:disable-line no-unused-variable max-line-length
}
