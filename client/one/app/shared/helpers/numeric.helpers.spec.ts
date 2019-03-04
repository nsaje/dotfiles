import * as numericHelpers from './numeric.helpers';

describe('numericHelpers', () => {
    it('should ignore all characters except digits', () => {
        expect(numericHelpers.parseInteger('abc234,.45')).toEqual('23445');
    });

    it('should ignore all characters except digits and period', () => {
        expect(numericHelpers.parseDecimal('abc234,.45789')).toEqual('234.46');
    });

    it('should append two decimal places by default', () => {
        expect(numericHelpers.parseDecimal('12.34567')).toEqual('12.35');
    });

    it('should take only first dot into account in case there are more', () => {
        expect(numericHelpers.parseDecimal('12.34.56')).toEqual('12.34');
        expect(numericHelpers.parseDecimal('12.3.4.56')).toEqual('12.30');
    });

    it('should correctly handle null, undefined and empty input parameter', () => {
        expect(numericHelpers.parseDecimal(null)).toEqual(null);
        expect(numericHelpers.parseDecimal(undefined)).toEqual(undefined);
        expect(numericHelpers.parseDecimal('')).toEqual('');
    });

    it('should correctly handle number sign', () => {
        expect(numericHelpers.parseDecimal('-1.7')).toEqual('-1.70');
        expect(numericHelpers.parseDecimal('+2.44')).toEqual('2.44');
        expect(numericHelpers.parseDecimal('-')).toEqual('0.00');
        expect(numericHelpers.parseDecimal('+')).toEqual('0.00');
    });

    it('should correctly return number sign', () => {
        expect(numericHelpers.getNumberSign(null)).toEqual('');
        expect(numericHelpers.getNumberSign(undefined)).toEqual('');
        expect(numericHelpers.getNumberSign(-1.1)).toEqual('-');
        expect(numericHelpers.getNumberSign(1.1)).toEqual('+');
    });

    it('should correctly validate if value is bigger than min and smaller than max', () => {
        expect(numericHelpers.validateMinMax(10, null, null)).toEqual(true);
        expect(numericHelpers.validateMinMax(10, 10, 10)).toEqual(true);
        expect(numericHelpers.validateMinMax(10, 9, 11)).toEqual(true);
        expect(numericHelpers.validateMinMax(10, 11, 12)).toEqual(false);
        expect(numericHelpers.validateMinMax(10, 8, 9)).toEqual(false);
        expect(numericHelpers.validateMinMax(10, 8, null)).toEqual(true);
        expect(numericHelpers.validateMinMax(10, null, 11)).toEqual(true);
        expect(numericHelpers.validateMinMax(10, 11, null)).toEqual(false);
        expect(numericHelpers.validateMinMax(10, null, 9)).toEqual(false);
    });
});
