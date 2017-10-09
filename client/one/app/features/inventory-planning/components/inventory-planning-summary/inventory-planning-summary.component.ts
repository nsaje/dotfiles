import './inventory-planning-summary.component.less';

import {Component, Input, OnChanges, ChangeDetectionStrategy} from '@angular/core';

import {CHART_X_AXIS_STEP, CHART_CONFIG} from './inventory-planning-summary.constants';

@Component({
    selector: 'zem-inventory-planning-summary',
    template: require('./inventory-planning-summary.component.html'),
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningSummaryComponent implements OnChanges {
    @Input() auctionCount: number;
    @Input() avgCpm: number;
    @Input() winRatio: number;
    @Input() isLoading: boolean;

    chartOptions: any = {};

    ngOnChanges (changes: any) {
        if (changes.avgCpm || changes.winRatio) {
            this.chartOptions = {
                ...CHART_CONFIG,
                series: getChartSeries(this.avgCpm, this.winRatio),
            };
        }
    }
}

function getChartSeries (avgCpm: number, winRatio: number): any {
    const data = calculateDataPoints(avgCpm, winRatio);
    return [{data: data}];
}

// FIXME (jurebajt): Add a test when a proper plotting function is implemented
function calculateDataPoints (avgCpm: number, winRatio: number): any {
    const data = [];
    const k = winRatio / avgCpm;
    let tmpCpm = 0;
    let tmpWinRatio = 0;
    data.push([0, 0]);
    while (tmpWinRatio < 1) {
        tmpCpm = tmpCpm + CHART_X_AXIS_STEP;
        tmpWinRatio = tmpCpm * k;
        data.push([tmpCpm.toFixed(3), tmpWinRatio * 100]); // tslint:disable-line no-magic-numbers
    }
    return data;
}
