import {PixelColumn} from '../../../../../../types/pixel-column';
import {AttributionColumnPickerStore} from './attribution-column-picker.store';
import {ConversionWindow} from '../../../../../../../../app.constants';

describe('AttributionColumnPickerStore', () => {
    let store: AttributionColumnPickerStore;
    let mockedPixelColumnsWithVisible: PixelColumn[];
    let mockedPixelColumnsWithoutVisible: PixelColumn[];

    beforeEach(() => {
        store = new AttributionColumnPickerStore();
        mockedPixelColumnsWithVisible = [
            {
                columns: [
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_24',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_295',
                            window: 24,
                        },
                        field: 'pixel_295_24',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_168',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_295',
                            window: 168,
                        },
                        field: 'pixel_295_168',
                        type: 'number',
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'View attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_24_view',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / View attribution',
                            pixel: 'pixel_295',
                            window: 24,
                        },
                        field: 'pixel_295_24_view',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_4927_720',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_4927',
                            window: 720,
                        },
                        field: 'pixel_4927_720',
                        type: 'number',
                        visible: false,
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
                            help:
                                'Number of completions of the conversion goal',
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
                        visible: false,
                    },
                ],
                description: undefined,
                name: 'BOR Nicole',
            },
        ];
        mockedPixelColumnsWithoutVisible = [
            {
                columns: [
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_24',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_295',
                            window: 24,
                        },
                        field: 'pixel_295_24',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_168',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_295',
                            window: 168,
                        },
                        field: 'pixel_295_168',
                        type: 'number',
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'View attribution',
                            performance: 'Conversions',
                            field: 'pixel_295_24_view',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / View attribution',
                            pixel: 'pixel_295',
                            window: 24,
                        },
                        field: 'pixel_295_24_view',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'Click attribution',
                            performance: 'Conversions',
                            field: 'pixel_4927_720',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / Click attribution',
                            pixel: 'pixel_4927',
                            window: 720,
                        },
                        field: 'pixel_4927_720',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                    {
                        data: {
                            attribution: 'View attribution',
                            performance: 'Conversions',
                            field: 'pixel_4927_24_view',
                            help:
                                'Number of completions of the conversion goal',
                            name: 'Conversions / View attribution',
                            pixel: 'pixel_4927',
                            window: 24,
                        },
                        field: 'pixel_4927_24_view',
                        type: 'number',
                        visible: false,
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
                        visible: false,
                    },
                ],
                description: undefined,
                name: 'BOR Nicole',
            },
        ];
    });

    it('should correctly set store', () => {
        store.setStore(mockedPixelColumnsWithVisible);
        const selectedPixel = mockedPixelColumnsWithVisible[1];
        expect(store.state.pixels).toEqual([selectedPixel]);
        expect(store.state.clickConversionWindow).toEqual({
            name: '30 days',
            value: ConversionWindow.LEQ_30_DAYS,
        });
        expect(store.state.viewConversionWindow).toEqual({
            name: '1 day',
            value: ConversionWindow.LEQ_1_DAY,
        });
        expect(store.state.metrics).toEqual([
            {attribution: 'Click attribution', performance: 'CPA'},
            {attribution: 'View attribution', performance: 'Conversions'},
        ]);
    });

    it('should correctly set pixels', () => {
        const selectedPixel = mockedPixelColumnsWithVisible[1];
        store.setPixels([selectedPixel]);
        expect(store.state.pixels).toEqual([selectedPixel]);
    });

    it('should correctly set click conversion window', () => {
        const selectedClickConversionWindow = {
            name: '7 day',
            value: ConversionWindow.LEQ_7_DAYS,
        };
        store.setClickConversionWindow(selectedClickConversionWindow);
        expect(store.state.clickConversionWindow).toEqual(
            selectedClickConversionWindow
        );
    });

    it('should correctly set view conversion window', () => {
        const selectedViewConversionWindow = {
            name: '1 day',
            value: ConversionWindow.LEQ_1_DAY,
        };
        store.setViewConversionWindow(selectedViewConversionWindow);
        expect(store.state.viewConversionWindow).toEqual(
            selectedViewConversionWindow
        );
    });

    it('should correctly add metric', () => {
        store.state.metrics = [
            {attribution: 'Click attribution', performance: 'CPA'},
        ];
        store.addMetric({
            attribution: 'View attribution',
            performance: 'Conversions',
        });
        expect(store.state.metrics).toEqual([
            {attribution: 'Click attribution', performance: 'CPA'},
            {attribution: 'View attribution', performance: 'Conversions'},
        ]);
    });

    it('should correctly remove metric', () => {
        store.state.metrics = [
            {attribution: 'Click attribution', performance: 'CPA'},
            {attribution: 'View attribution', performance: 'Conversions'},
        ];
        store.removeMetric({
            attribution: 'View attribution',
            performance: 'Conversions',
        });
        expect(store.state.metrics).toEqual([
            {attribution: 'Click attribution', performance: 'CPA'},
        ]);
    });
});
