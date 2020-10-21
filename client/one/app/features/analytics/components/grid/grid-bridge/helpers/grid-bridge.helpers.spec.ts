import {Currency} from '../../../../../../app.constants';
import {GridColumnTypes} from '../../../../analytics.constants';
import {MIN_COLUMN_WIDTH} from '../grid-bridge.component.constants';
import * as gridBridgeHelpers from './grid-bridge.helpers';

describe('GridBridgeHelpers', () => {
    const CUSTOM_MIN_COLUMN_WIDTH = 50;
    const CUSTOM_NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN = 10;
    const CUSTOM_NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN = 50;

    it('should correctly compute approximate grid column width with default values', () => {
        expect(gridBridgeHelpers.getApproximateGridColumnWidth('')).toEqual(
            MIN_COLUMN_WIDTH
        );
        expect(gridBridgeHelpers.getApproximateGridColumnWidth(null)).toEqual(
            MIN_COLUMN_WIDTH
        );
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth(undefined)
        ).toEqual(MIN_COLUMN_WIDTH);
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth('Test Column Name')
        ).toEqual(162);
    });

    it('should correctly compute approximate grid column width', () => {
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth(
                '',
                CUSTOM_MIN_COLUMN_WIDTH,
                CUSTOM_NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
                CUSTOM_NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
            )
        ).toEqual(CUSTOM_MIN_COLUMN_WIDTH);
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth(
                null,
                CUSTOM_MIN_COLUMN_WIDTH,
                CUSTOM_NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
                CUSTOM_NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
            )
        ).toEqual(CUSTOM_MIN_COLUMN_WIDTH);
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth(
                undefined,
                CUSTOM_MIN_COLUMN_WIDTH,
                CUSTOM_NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
                CUSTOM_NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
            )
        ).toEqual(CUSTOM_MIN_COLUMN_WIDTH);
        expect(
            gridBridgeHelpers.getApproximateGridColumnWidth(
                'Test Column Name',
                CUSTOM_MIN_COLUMN_WIDTH,
                CUSTOM_NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
                CUSTOM_NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
            )
        ).toEqual(210);
    });

    it('should correctly format grid column value (corner case)', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.ACTIONS,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.ACTIONS,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.ACTIONS,
                defaultValue: 'Test',
            })
        ).toEqual('Test');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.ACTIONS,
                defaultValue: 'Test',
            })
        ).toEqual('Test');
        expect(
            gridBridgeHelpers.formatGridColumnValue('Test', {
                type: GridColumnTypes.ACTIONS,
            })
        ).toEqual('Test');
        expect(
            gridBridgeHelpers.formatGridColumnValue(12345, {
                type: GridColumnTypes.ACTIONS,
            })
        ).toEqual('12345');
    });

    it('should correctly format grid column text value', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.TEXT,
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.TEXT,
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.TEXT,
                defaultValue: 'N/A',
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.TEXT,
                defaultValue: 'N/A',
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue('Test', {
                type: GridColumnTypes.TEXT,
            })
        ).toEqual('Test');
    });

    it('should correctly format grid column percent value', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.PERCENT,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.PERCENT,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.PERCENT,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.PERCENT,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(5, {
                type: GridColumnTypes.PERCENT,
            })
        ).toEqual('5.00%');
    });

    it('should correctly format grid column seconds value', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.SECONDS,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.SECONDS,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.SECONDS,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.SECONDS,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(10, {
                type: GridColumnTypes.SECONDS,
            })
        ).toEqual('10.0s');
    });

    it('should correctly format grid column number value', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.NUMBER,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.NUMBER,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.NUMBER,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.NUMBER,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(10, {
                type: GridColumnTypes.NUMBER,
            })
        ).toEqual('10');
    });

    it('should correctly format grid column currency value', () => {
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.CURRENCY,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.CURRENCY,
            })
        ).toEqual('N/A');
        expect(
            gridBridgeHelpers.formatGridColumnValue(undefined, {
                type: GridColumnTypes.CURRENCY,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(null, {
                type: GridColumnTypes.CURRENCY,
                defaultValue: '',
            })
        ).toEqual('');
        expect(
            gridBridgeHelpers.formatGridColumnValue(10, {
                type: GridColumnTypes.CURRENCY,
            })
        ).toEqual('$10.00');
        expect(
            gridBridgeHelpers.formatGridColumnValue(10, {
                type: GridColumnTypes.CURRENCY,
                currency: Currency.EUR,
            })
        ).toEqual('€10.00');
    });
});
