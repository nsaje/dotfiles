import {ConversionPixelKPIConfig} from '../../../../../../core/conversion-pixels/types/conversion-pixel-kpi-config';
import {PixelOption} from './types/pixel-option';
import {
    ConversionPixelAttribution,
    ConversionPixelKPI,
} from '../../../../../../core/conversion-pixels/conversion-pixel.constants';
import {ConversionWindow} from '../../../../../../app.constants';
import {CONVERSION_WINDOW_NUMBER_FORMAT} from '../../../../../../app.config';

export const CONVERSION_PIXEL_KPIS: ConversionPixelKPIConfig[] = [
    {
        name: 'Conversions',
        value: ConversionPixelKPI.CONVERSIONS,
    },
    {
        name: 'CPA',
        value: ConversionPixelKPI.CPA,
    },
    {
        name: 'Conversion rate',
        value: ConversionPixelKPI.CONVERSION_RATE,
    },
];

export const CONVERSION_PIXEL_OPTIONS: PixelOption[] = [
    {
        name: '1 day click attribution',
        attribution: ConversionPixelAttribution.CLICK,
        window: CONVERSION_WINDOW_NUMBER_FORMAT[ConversionWindow.LEQ_1_DAY],
    },
    {
        name: '7 days click attribution',
        attribution: ConversionPixelAttribution.CLICK,
        window: CONVERSION_WINDOW_NUMBER_FORMAT[ConversionWindow.LEQ_7_DAYS],
    },
    {
        name: '30 days click attribution',
        attribution: ConversionPixelAttribution.CLICK,
        window: CONVERSION_WINDOW_NUMBER_FORMAT[ConversionWindow.LEQ_30_DAYS],
    },
    {
        name: '1 day view attribution',
        attribution: ConversionPixelAttribution.VIEW,
        window: CONVERSION_WINDOW_NUMBER_FORMAT[ConversionWindow.LEQ_1_DAY],
    },
];
