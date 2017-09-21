import './inventory-planning-summary.component.less';

import {Component, Input, ChangeDetectionStrategy} from '@angular/core';


@Component({
    selector: 'zem-inventory-planning-summary',
    template: require('./inventory-planning-summary.component.html'),
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningSummaryComponent {
    @Input() auctionCount: number;
    @Input() avgCpm: number;
}
