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
});
