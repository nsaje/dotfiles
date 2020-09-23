import {RuleConditionOperandType, TimeRange} from '../rules.constants';
import {ConversionWindow} from '../../../app.constants';
import {ConversionPixelAttribution} from '../../conversion-pixels/conversion-pixel.constants';

export interface RuleConditionMetric {
    type: RuleConditionOperandType;
    window: TimeRange;
    modifier: string;
    conversionPixel?: string;
    conversionPixelWindow?: ConversionWindow;
    conversionPixelAttribution?: ConversionPixelAttribution;
}
