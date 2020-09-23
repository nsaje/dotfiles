import './rule-edit-form-condition-conversion-pixel.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    SimpleChanges,
    OnChanges,
    OnInit,
} from '@angular/core';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {ConversionWindow} from '../../../../app.constants';
import {ConversionWindowConfig} from '../../../../core/conversion-pixels/types/conversion-windows-config';
import {ConversionPixelAttribution} from '../../../../core/conversion-pixels/conversion-pixel.constants';
import {ConversionPixelAttributionConfig} from '../../../../core/conversion-pixels/types/conversion-pixel-attribution-config';
import {
    CONVERSION_PIXEL_ATTRIBUTIONS,
    CONVERSION_PIXEL_CLICK_WINDOWS,
    CONVERSION_PIXEL_VIEW_WINDOWS,
    CONVERSION_PIXEL_TOTAL_WINDOWS,
} from '../../../../core/conversion-pixels/conversion-pixels.config';
import {ConversionPixelOptions} from './rule-edit-form-condition-conversion-pixel.config';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {RuleConditionMetricError} from '../rule-edit-form/types/rule-condition-metric-error';

@Component({
    selector: 'zem-rule-edit-form-condition-conversion-pixel',
    templateUrl: './rule-edit-form-condition-conversion-pixel.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormConditionConversionPixelComponent
    implements OnInit, OnChanges {
    @Input()
    availableConversionPixels: ConversionPixel[];
    @Input()
    conversionPixel: string;
    @Input()
    conversionPixelWindow: ConversionWindow;
    @Input()
    conversionPixelAttribution: ConversionPixelAttribution;
    @Input()
    isDisabled: boolean = false;
    @Input()
    metricErrors: RuleConditionMetricError;
    @Output()
    pixelChange = new EventEmitter<string>();
    @Output()
    windowChange = new EventEmitter<ConversionWindow>();
    @Output()
    attributionChange = new EventEmitter<ConversionPixelAttribution>();
    @Output()
    conversionPixelsSearch = new EventEmitter<string>();

    conversionWindows: ConversionWindowConfig[] = CONVERSION_PIXEL_CLICK_WINDOWS;
    conversionAttributions: ConversionPixelAttributionConfig[] = CONVERSION_PIXEL_ATTRIBUTIONS;

    ConversionPixelOptions = ConversionPixelOptions;
    conversionPixelOption: ConversionPixelOptions;

    ngOnInit() {
        if (commonHelpers.isDefined(this.conversionPixel)) {
            this.conversionPixelsSearch.emit(null);
            this.conversionPixelOption = ConversionPixelOptions.PIXEL;
        } else {
            this.conversionPixelOption = ConversionPixelOptions.CAMPAIGN_GOAL;
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.conversionPixelAttribution) {
            switch (this.conversionPixelAttribution) {
                case ConversionPixelAttribution.CLICK:
                    this.conversionWindows = CONVERSION_PIXEL_CLICK_WINDOWS;
                    break;
                case ConversionPixelAttribution.VIEW:
                    this.conversionWindows = CONVERSION_PIXEL_VIEW_WINDOWS;
                    break;
                case ConversionPixelAttribution.TOTAL:
                    this.conversionWindows = CONVERSION_PIXEL_TOTAL_WINDOWS;
                    break;
            }
        }
    }

    changeConversionPixelOption(option: ConversionPixelOptions) {
        this.conversionPixelOption = option;
        if (option === ConversionPixelOptions.CAMPAIGN_GOAL) {
            this.pixelChange.emit(null);
        }
    }
}
