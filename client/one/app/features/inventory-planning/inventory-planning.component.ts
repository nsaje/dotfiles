import './inventory-planning.component.less';

import {Component, Inject} from '@angular/core';

import {InventoryPlanningStore} from './inventory-planning.store';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';

@Component({
    selector: 'zem-inventory-planning',
    template: require('./inventory-planning.component.html'),
    providers: [InventoryPlanningStore, InventoryPlanningEndpoint],
})
export class InventoryPlanningComponent {
    constructor (private store: InventoryPlanningStore, // tslint:disable-line no-unused-variable
                 @Inject('zemPermissions') private zemPermissions: any) {} // tslint:disable-line no-unused-variable
}
