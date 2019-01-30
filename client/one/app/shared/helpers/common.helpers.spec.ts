import * as commonHelpers from './common.helpers';

describe('CommonHelpers', () => {
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

    it('should correctly insert value at specified index', () => {
        expect(commonHelpers.insertStringAtIndex('123', 0, '999')).toEqual(
            '999123'
        );
        expect(commonHelpers.insertStringAtIndex('123', 1, '999')).toEqual(
            '199923'
        );
        expect(commonHelpers.insertStringAtIndex('123', 2, '999')).toEqual(
            '129993'
        );
        expect(commonHelpers.insertStringAtIndex('123', 3, '999')).toEqual(
            '123999'
        );
        expect(commonHelpers.insertStringAtIndex(null, 3, '999')).toEqual(
            '999'
        );
        expect(commonHelpers.insertStringAtIndex(undefined, 3, '999')).toEqual(
            '999'
        );
        expect(commonHelpers.insertStringAtIndex('', 3, '999')).toEqual('999');
    });
});
