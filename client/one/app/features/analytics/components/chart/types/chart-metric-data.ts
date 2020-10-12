import {CostMode, Currency} from '../../../../../app.constants';
import {
    ConversionPixelAttribution,
    ConversionPixelKPI,
} from '../../../../../core/conversion-pixels/conversion-pixel.constants';

export interface ChartMetricData {
    name?: string;
    value: string;
    type?: 'number' | 'currency' | 'time';
    currency?: Currency;
    internal?: boolean;
    shown: boolean;
    costMode?: CostMode;
    fractionSize?: number;
    pixel?: string;
    window?: number;
    attribution?: ConversionPixelAttribution;
    performance?: ConversionPixelKPI;
}
