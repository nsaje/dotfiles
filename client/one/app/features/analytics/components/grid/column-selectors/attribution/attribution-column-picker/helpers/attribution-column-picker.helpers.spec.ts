import * as attributionColumnHelpers from './attribution-column-picker.helpers';
import {PixelColumn} from '../../../../../../types/pixel-column';
import {ConversionWindow} from '../../../../../../../../app.constants';

describe('AttributionColumnPickerHelpers', () => {
    const mockedPixels: PixelColumn[] = [
        {
            columns: [
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'Conversions',
                        field: 'pixel_295_24',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'CPA',
                        field: 'avg_etfm_cost_per_pixel_295_24',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_295_24',
                    type: 'currency',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'Conversions',
                        field: 'pixel_295_168',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 168,
                    },
                    field: 'pixel_295_168',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'View attribution',
                        performance: 'Conversions',
                        field: 'pixel_295_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24_view',
                    type: 'number',
                    visible: true,
                },
            ],
            description: undefined,
            name: 'Book Sale',
        },
        {
            columns: [
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'CPA',
                        field: 'avg_etfm_cost_per_pixel_4927_168',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 168,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_168',
                    type: 'currency',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'Conversions',
                        field: 'pixel_4927_720',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'pixel_4927_720',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'Click attribution',
                        performance: 'CPA',
                        field: 'avg_etfm_cost_per_pixel_4927_720',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    type: 'currency',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'View attribution',
                        performance: 'Conversions',
                        field: 'pixel_4927_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'pixel_4927_24_view',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: 'View attribution',
                        performance: 'CPA',
                        field: 'avg_etfm_cost_per_pixel_4927_24_view',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_24_view',
                    type: 'currency',
                    visible: true,
                },
            ],
            description: undefined,
            name: 'BOR Nicole',
        },
    ];

    it('should correctly return all fields', () => {
        const allFields = attributionColumnHelpers.getAllFields(
            mockedPixels,
            [{name: '7 days', value: ConversionWindow.LEQ_7_DAYS}],
            [{name: '1 day', value: ConversionWindow.LEQ_1_DAY}],
            [
                {
                    attribution: 'Click attribution',
                    performance: 'CPA',
                },
                {
                    attribution: 'View attribution',
                    performance: 'Conversions',
                },
            ]
        );
        expect(allFields).toEqual([
            'pixel_295_24_view',
            'avg_etfm_cost_per_pixel_4927_168',
            'pixel_4927_24_view',
        ]);
    });

    it('should correctly return empty value', () => {
        const allFields = attributionColumnHelpers.getAllFields(
            mockedPixels,
            [{name: '7 days', value: ConversionWindow.LEQ_7_DAYS}],
            [{name: '1 day', value: ConversionWindow.LEQ_1_DAY}],
            []
        );
        expect(allFields).toEqual([]);
    });
});
