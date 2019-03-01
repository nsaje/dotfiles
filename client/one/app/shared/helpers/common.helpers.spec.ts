import * as commonHelpers from './common.helpers';

describe('commonHelpers', () => {
    it('should correctly check if value is defined', () => {
        expect(commonHelpers.isDefined(null)).toEqual(false);
        expect(commonHelpers.isDefined(undefined)).toEqual(false);
        expect(commonHelpers.isDefined('Test')).toEqual(true);
        expect(commonHelpers.isDefined(123)).toEqual(true);
    });

    it('should correctly return value if defined, otherwise should return default', () => {
        expect(commonHelpers.getValueOrDefault(999, 123)).toEqual(999);
        expect(commonHelpers.getValueOrDefault(null, 123)).toEqual(123);
        expect(commonHelpers.getValueOrDefault('Test', 'Default')).toEqual(
            'Test'
        );
        expect(commonHelpers.getValueOrDefault(undefined, 'Default')).toEqual(
            'Default'
        );
    });
});
