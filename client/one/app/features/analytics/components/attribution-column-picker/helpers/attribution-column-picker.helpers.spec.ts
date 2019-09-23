import * as attributionColumnHelpers from './attribution-column-picker.helpers';
import {PixelOptionsColumn} from '../../../types/pixel-options-column';

describe('AttributionColumnPickerHelpers', () => {
    const mockedSelectedColumns: PixelOptionsColumn[] = [
        {
            data: {
                attribution: '',
                field: 'pixel_4927_168',
                help: 'Number of completions of the conversion goal',
                name: 'Conversions / Click attribution',
                pixel: 'pixel_4927',
                window: 168,
            },
            field: 'pixel_4927_168',
            type: 'number',
            visible: true,
        },
        {
            data: {
                attribution: '',
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
    ];

    it('should correctly return empty fieldsToToggle when selectedColumns are empty', () => {
        const fieldsToToggle = attributionColumnHelpers.getFieldsToToggle(
            [],
            /pixel_1/,
            'pixel_2'
        );

        expect(fieldsToToggle).toEqual([]);
    });

    it('should correctly return fieldsToToggle', () => {
        const fieldsToToggle = attributionColumnHelpers.getFieldsToToggle(
            mockedSelectedColumns,
            /_168$/,
            '_24'
        );

        expect(fieldsToToggle).toEqual([
            'pixel_4927_168',
            'pixel_4927_24',
            'avg_etfm_cost_per_pixel_4927_168',
            'avg_etfm_cost_per_pixel_4927_24',
        ]);
    });
});
