import './inventory-planning-summary.component.less';

import {Component, Input, OnChanges, ChangeDetectionStrategy, SimpleChanges} from '@angular/core';

import {CHART_X_AXIS_STEP, MAX_PLOTTED_CPM, CHART_CONFIG} from './inventory-planning-summary.constants';

@Component({
    selector: 'zem-inventory-planning-summary',
    templateUrl: './inventory-planning-summary.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningSummaryComponent implements OnChanges {
    @Input() auctionCount: number;
    @Input() avgCpm: number;
    @Input() winRatio: number;
    @Input() isLoading: boolean;

    chartOptions: any = {};

    ngOnChanges (changes: SimpleChanges) {
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

function calculateDataPoints (avgCpm: number, winRatio: number): any {
    // tslint:disable no-magic-numbers
    if (!avgCpm || !winRatio) {
        return null;
    }
    const k = 50 * winRatio / Math.log(15 * avgCpm);

    let tmpCpm = 0;
    let tmpWinRatio = 0;
    const data = [];

    while (tmpCpm <= MAX_PLOTTED_CPM && tmpWinRatio < 1) {
        tmpWinRatio = k * (Math.log(15 * tmpCpm + 1) / 5);
        if (tmpWinRatio > 1) {
            tmpWinRatio = 1;
        }
        data.push([parseFloat(tmpCpm.toFixed(2)), parseFloat((tmpWinRatio * 100).toFixed(2))]);
        tmpCpm = tmpCpm + CHART_X_AXIS_STEP;
    }

    return data;
    // tslint:enable no-magic-numbers
}
