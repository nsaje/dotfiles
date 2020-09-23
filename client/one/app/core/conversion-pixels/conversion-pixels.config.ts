import {APP_CONFIG} from '../../app.config';
import {ConversionPixelAttribution} from './conversion-pixel.constants';
import {ConversionPixelAttributionConfig} from './types/conversion-pixel-attribution-config';
import {ConversionWindowConfig} from './types/conversion-windows-config';
import {ConversionWindow} from '../../app.constants';

const conversionPixelsApiUrl = `${APP_CONFIG.apiRestInternalUrl}/pixels/`;

export const CONVERSION_PIXELS_CONFIG = {
    requests: {
        conversionPixels: {
            list: {
                name: 'list',
                url: conversionPixelsApiUrl,
            },
            create: {
                name: 'create',
                url: conversionPixelsApiUrl,
            },
            edit: {
                name: 'edit',
                url: `${conversionPixelsApiUrl}{conversionPixelId}`,
            },
        },
    },
};

export const CONVERSION_PIXEL_ATTRIBUTIONS: ConversionPixelAttributionConfig[] = [
    {name: 'Click', value: ConversionPixelAttribution.CLICK},
    {name: 'View', value: ConversionPixelAttribution.VIEW},
    {name: 'Total (click + view)', value: ConversionPixelAttribution.TOTAL},
];

export const CONVERSION_PIXEL_CLICK_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day', value: ConversionWindow.LEQ_1_DAY},
    {name: '7 days', value: ConversionWindow.LEQ_7_DAYS},
    {name: '30 days', value: ConversionWindow.LEQ_30_DAYS},
];

export const CONVERSION_PIXEL_VIEW_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day', value: ConversionWindow.LEQ_1_DAY},
];

export const CONVERSION_PIXEL_TOTAL_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day click and 1 day view', value: ConversionWindow.LEQ_1_DAY},
    {name: '7 days click and 1 day view', value: ConversionWindow.LEQ_7_DAYS},
    {name: '30 days click and 1 day view', value: ConversionWindow.LEQ_30_DAYS},
];
