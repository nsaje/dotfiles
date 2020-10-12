import './conversion-pixel-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ConversionPixelKPI} from '../../../../../../core/conversion-pixels/conversion-pixel.constants';
import {ConversionPixelKPIConfig} from '../../../../../../core/conversion-pixels/types/conversion-pixel-kpi-config';
import {PixelOption} from './types/pixel-option';
import {ChartMetricData} from '../../types/chart-metric-data';
import {ChartCategory} from '../../types/chart-category';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {
    CONVERSION_PIXEL_OPTIONS,
    CONVERSION_PIXEL_KPIS,
} from './conversion-pixel-selector-component.config';

@Component({
    selector: 'zem-conversion-pixel-selector',
    templateUrl: './conversion-pixel-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConversionPixelSelectorComponent implements OnChanges {
    @Input()
    selectedMetric: ChartMetricData;
    @Input()
    pixelCategories: ChartCategory[];
    @Output()
    valueChange = new EventEmitter<ChartMetricData>();

    CONVERSION_PIXEL_KPIS: ConversionPixelKPIConfig[] = CONVERSION_PIXEL_KPIS;
    CONVERSION_PIXEL_OPTIONS: PixelOption[] = CONVERSION_PIXEL_OPTIONS;

    selectedPixel: ChartCategory;
    selectedKPI: ConversionPixelKPI;
    selectedOption: PixelOption;

    ngOnChanges(changes: SimpleChanges) {
        if (
            changes.selectedMetric &&
            commonHelpers.isDefined(this.selectedMetric?.pixel)
        ) {
            this.selectedPixel = this.pixelCategories.find(
                pixel => pixel.name === this.selectedMetric.pixel
            );
            this.selectedKPI = this.selectedMetric.performance;
            this.selectedOption = this.CONVERSION_PIXEL_OPTIONS.find(
                option =>
                    option.attribution === this.selectedMetric.attribution &&
                    option.window === this.selectedMetric.window
            );
        }
    }

    onPixelChange(pixelName: string) {
        this.selectedPixel = this.pixelCategories.find(
            (pixel: ChartCategory) => pixel.name === pixelName
        );
    }

    onPixelOptionChange(optionName: string) {
        this.selectedOption = this.CONVERSION_PIXEL_OPTIONS.find(
            (option: PixelOption) => option.name === optionName
        );
    }

    selectConversionPixelMetrics() {
        const selectedMetrics: ChartMetricData = this.selectedPixel.metrics.find(
            (metric: ChartMetricData) => {
                return (
                    metric.performance === this.selectedKPI &&
                    metric.window === this.selectedOption.window &&
                    metric.attribution === this.selectedOption.attribution
                );
            }
        );
        this.valueChange.emit(selectedMetrics);
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemConversionPixelSelector',
    downgradeComponent({
        component: ConversionPixelSelectorComponent,
        inputs: ['pixelColumns'],
        outputs: ['valueChange'],
        propagateDigest: false,
    })
);
