import {Component} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-inventory-planning-view',
    template: require('./inventory-planning.view.html'),
})
export class InventoryPlanningViewComponent {
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemInventoryPlanningView',
    downgradeComponent({component: InventoryPlanningViewComponent}) as angular.IDirectiveFactory
);
