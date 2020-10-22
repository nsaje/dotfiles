import {Currency} from '../../../../../../app.constants';
import {GridColumnTypes} from '../../../../analytics.constants';
import * as gridBridgeHelpers from './grid-bridge.helpers';

describe('GridBridgeHelpers', () => {
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
