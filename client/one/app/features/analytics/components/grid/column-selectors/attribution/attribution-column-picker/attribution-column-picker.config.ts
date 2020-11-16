import PixelMetric from './types/pixel-metric';

export const METRICS_OPTIONS_CLICK: PixelMetric[] = [
    {attribution: 'Click attribution', performance: 'Conversions'},
    {attribution: 'Click attribution', performance: 'Conversion rate'},
    {attribution: 'Click attribution', performance: 'CPA'},
    {
        attribution: 'Click attribution',
        performance: 'ROAS',
    },
];

export const METRICS_OPTIONS_VIEW: PixelMetric[] = [
    {attribution: 'View attribution', performance: 'Conversions'},
    {
        attribution: 'View attribution',
        performance: 'Conversion rate',
    },
    {attribution: 'View attribution', performance: 'CPA'},
    {
        attribution: 'View attribution',
        performance: 'ROAS',
    },
];
